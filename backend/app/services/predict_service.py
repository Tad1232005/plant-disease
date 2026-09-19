"""Inference nhiều model với temperature scaling và soft-voting."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import io
import json
import math
from pathlib import Path
from threading import BoundedSemaphore, Lock
import time
from typing import Any, Literal, Sequence
import logging
from collections import OrderedDict

import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from sqlalchemy.orm import Session
from torchvision import models, transforms

from app.core.config import settings
from app.models.model_version import ModelVersion
from app.services.model_artifact_service import load_artifact

logger = logging.getLogger(__name__)

InferenceMode = Literal["basic", "standard", "advanced"]
RequestedMode = Literal["auto", "basic", "standard", "advanced"]

MODEL_TYPES_BY_MODE: dict[InferenceMode, tuple[str, ...]] = {
    "basic": ("efficientnet_b0",),
    "standard": ("efficientnet_b0", "mobilenet_v2"),
    "advanced": ("efficientnet_b0", "mobilenet_v2", "resnet50"),
}
MAX_MODE_BY_ROLE: dict[str | None, InferenceMode] = {
    None: "basic",
    "user": "standard",
    "manager": "standard",
    "technician": "advanced",
    "admin": "advanced",
}
MODE_RANK: dict[InferenceMode, int] = {
    "basic": 1, "standard": 2, "advanced": 3
}
POLICY_VERSION = "ensemble-rgb224-v3-selection"


class ModelConfigurationError(RuntimeError):
    """Cấu hình DB/artifact không đủ để chạy mode đã chọn."""


class ModeNotAllowedError(ValueError):
    """Role yêu cầu mode cao hơn capability được cấp."""


class InferenceCapacityError(RuntimeError):
    """Hệ thống đã dùng hết số inference slot được cấu hình."""


@dataclass(frozen=True)
class ActiveModelSpec:
    id: int
    version_name: str
    model_type: str
    file_path: str
    classes_path: str
    temperature: float
    sha256: str | None


def resolve_mode(role: str | None, requested: RequestedMode) -> InferenceMode:
    """Ánh xạ role -> mode tối đa và chặn nâng quyền bằng input client."""
    max_mode = MAX_MODE_BY_ROLE.get(role)
    if max_mode is None:
        raise ModeNotAllowedError("Role không được phép dùng inference")
    if requested == "auto":
        return max_mode
    if MODE_RANK[requested] > MODE_RANK[max_mode]:
        raise ModeNotAllowedError(
            f"Role hiện tại chỉ được dùng tối đa mode '{max_mode}'"
        )
    return requested


def capabilities_for_role(role: str | None) -> dict[str, Any]:
    max_mode = MAX_MODE_BY_ROLE.get(role, "basic")
    modes: list[InferenceMode] = [
        name for name, rank in MODE_RANK.items() if rank <= MODE_RANK[max_mode]
    ]
    return {
        "role": role or "guest",
        "default_mode": max_mode,
        "allowed_modes": modes,
        "models_by_mode": {mode: list(MODEL_TYPES_BY_MODE[mode]) for mode in modes},
        "allowed_model_types": list(MODEL_TYPES_BY_MODE[max_mode]),
        "policy_version": POLICY_VERSION,
    }


def get_active_models(db: Session, mode: InferenceMode, model_type: str | None = None) -> list[ActiveModelSpec]:
    """Lấy đúng active version của từng model type theo thứ tự policy."""
    if model_type is not None and model_type not in MODEL_TYPES_BY_MODE[mode]:
        raise ModeNotAllowedError(f"Mode {mode} không được dùng model {model_type}")
    required = (model_type,) if model_type is not None else MODEL_TYPES_BY_MODE[mode]
    rows = (
        db.query(ModelVersion)
        .filter(
            ModelVersion.model_type.in_(required),
            ModelVersion.is_active.is_(True),
            ModelVersion.is_enabled.is_(True),
        )
        .all()
    )
    by_type = {row.model_type: row for row in rows}
    missing = [model_type for model_type in required if model_type not in by_type]
    if missing:
        raise ModelConfigurationError(
            "Thiếu active model version: " + ", ".join(missing)
        )
    invalid = [
        model_type
        for model_type in required
        if not by_type[model_type].classes_path
        or not by_type[model_type].sha256
        or len(by_type[model_type].sha256 or "") != 64
    ]
    if invalid:
        raise ModelConfigurationError(
            "Active model thiếu classes/checksum: " + ", ".join(invalid)
        )
    return [
        ActiveModelSpec(
            id=by_type[model_type].id,
            version_name=by_type[model_type].version_name,
            model_type=model_type,
            file_path=by_type[model_type].file_path,
            classes_path=by_type[model_type].classes_path or "",
            temperature=by_type[model_type].temperature,
            sha256=by_type[model_type].sha256,
        )
        for model_type in required
    ]


@dataclass
class LoadedModel:
    model: nn.Module
    classes: list[str]


class PredictService:
    """Cache model theo version và tổng hợp calibrated probabilities."""

    def __init__(self) -> None:
        if settings.MAX_CONCURRENT_INFERENCES < 1:
            raise ValueError("MAX_CONCURRENT_INFERENCES phải lớn hơn hoặc bằng 1")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._cache: OrderedDict[ActiveModelSpec, LoadedModel] = OrderedDict()
        self._load_lock = Lock()
        self._capacity = BoundedSemaphore(settings.MAX_CONCURRENT_INFERENCES)
        # Dùng chung executor giữa các request để không tạo 2-3 thread mới
        # cho mỗi lần gọi Standard/Advanced.
        self._model_executor = ThreadPoolExecutor(
            max_workers=3,
            thread_name_prefix="plant-model",
        )
        self.transform = transforms.Compose(
            [
                transforms.Resize((224, 224), interpolation=transforms.InterpolationMode.BILINEAR, antialias=True),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ]
        )

    @staticmethod
    def _build_model(model_type: str, class_count: int) -> nn.Module:
        if model_type == "mobilenet_v2":
            model = models.mobilenet_v2(weights=None)
            model.classifier[1] = nn.Linear(model.classifier[1].in_features, class_count)
            return model
        if model_type == "efficientnet_b0":
            model = models.efficientnet_b0(weights=None)
            model.classifier[1] = nn.Linear(model.classifier[1].in_features, class_count)
            return model
        if model_type == "resnet50":
            model = models.resnet50(weights=None)
            model.fc = nn.Linear(model.fc.in_features, class_count)
            return model
        raise ModelConfigurationError(f"model_type chưa được hỗ trợ: {model_type}")

    def _load(self, spec: ActiveModelSpec) -> LoadedModel:
        key = spec
        with self._load_lock:
            cached = self._cache.get(key)
            if cached is not None:
                self._cache.move_to_end(key)
                return cached
            try:
                if not math.isfinite(spec.temperature) or spec.temperature <= 0:
                    raise ValueError("Temperature phải hữu hạn và dương")
                if spec.sha256:
                    artifact = load_artifact(
                        Path(spec.file_path).parent / "manifest.json"
                    )
                    if (
                        artifact.sha256 != spec.sha256
                        or artifact.version_name != spec.version_name
                        or artifact.model_type != spec.model_type
                        or Path(artifact.file_path) != Path(spec.file_path).resolve()
                        or Path(artifact.classes_path) != Path(spec.classes_path).resolve()
                        or not math.isclose(
                            artifact.temperature, spec.temperature, rel_tol=1e-9
                        )
                    ):
                        raise ValueError("Artifact hiện tại không khớp metadata DB")
                classes_raw = json.loads(Path(spec.classes_path).read_text(encoding="utf-8"))
                if (not isinstance(classes_raw, list) or len(classes_raw) < 2
                        or any(not isinstance(label, str) or not label.strip() for label in classes_raw)
                        or len(set(classes_raw)) != len(classes_raw)):
                    raise ValueError("classes.json phải chứa ít nhất hai nhãn duy nhất")
                classes = [str(item) for item in classes_raw]
                model = self._build_model(spec.model_type, len(classes))
                state_dict = torch.load(
                    Path(spec.file_path), map_location=self.device, weights_only=True
                )
                model.load_state_dict(state_dict, strict=True)
                model.to(self.device)
                model.eval()
            except (OSError, ValueError, json.JSONDecodeError, RuntimeError) as exc:
                raise ModelConfigurationError(
                    f"Không thể load artifact {spec.version_name}"
                ) from exc
            loaded = LoadedModel(model=model, classes=classes)
            self._cache[key] = loaded
            while len(self._cache) > 6:
                self._cache.popitem(last=False)
            return loaded

    def _predict_one(self, tensor: torch.Tensor, spec: ActiveModelSpec) -> dict[str, Any]:
        started = time.perf_counter()
        loaded = self._load(spec)
        with torch.no_grad():
            logits = loaded.model(tensor)
            if logits.shape != (1, len(loaded.classes)) or not torch.isfinite(logits).all():
                raise ModelConfigurationError("Logits không hợp lệ")
            calibrated_logits = logits / spec.temperature
            probs = F.softmax(calibrated_logits, dim=1)[0].detach().cpu()
            energy = float(-spec.temperature * torch.logsumexp(calibrated_logits[0], dim=0))
        topk_conf, topk_idx = torch.topk(probs, k=min(3, len(loaded.classes)))
        confidence = float(topk_conf[0])
        margin = confidence - (float(topk_conf[1]) if len(topk_conf) > 1 else 0.0)
        entropy = float(-(probs * torch.log(probs.clamp_min(1e-12))).sum()) / math.log(len(probs))
        top_k = [
            {
                "label": loaded.classes[int(idx)],
                "confidence": round(float(conf), 6),
                "rank": rank,
            }
            for rank, (conf, idx) in enumerate(zip(topk_conf, topk_idx), start=1)
        ]
        return {
            "model_version_id": spec.id,
            "version_name": spec.version_name,
            "model_type": spec.model_type,
            "predicted_label": top_k[0]["label"],
            "confidence": round(confidence, 6),
            "top1_top2_margin": round(margin, 6),
            "entropy": round(entropy, 6),
            "energy_score": round(energy, 6),
            "accepted": confidence >= settings.CONFIDENCE_THRESHOLD and margin >= settings.TOP1_MARGIN_THRESHOLD,
            "latency_ms": round((time.perf_counter() - started) * 1000, 3),
            "error_code": None,
            "top_k": top_k,
            "all_probs": probs.tolist(),
            "classes": loaded.classes,
        }

    def _safe_predict_one(
        self, tensor: torch.Tensor, spec: ActiveModelSpec, order: int
    ) -> dict[str, Any]:
        try:
            result = self._predict_one(tensor, spec)
            result["execution_order"] = order
            return result
        except Exception:
            logger.exception(
                "Inference failed for model version %s", spec.version_name
            )
            return {
                "model_version_id": spec.id,
                "version_name": spec.version_name,
                "model_type": spec.model_type,
                "execution_order": order,
                "predicted_label": None,
                "confidence": None,
                "top1_top2_margin": None,
                "entropy": None,
                "energy_score": None,
                "accepted": False,
                "latency_ms": None,
                "error_code": "inference_failed",
                "top_k": [],
            }

    @staticmethod
    def _js_divergence(probabilities: Sequence[torch.Tensor]) -> float:
        if len(probabilities) < 2:
            return 0.0
        stacked = torch.stack(list(probabilities))
        mean = stacked.mean(dim=0).clamp_min(1e-12)
        kl = (stacked * (torch.log(stacked.clamp_min(1e-12)) - torch.log(mean))).sum(dim=1)
        return min(1.0, max(0.0, float(kl.mean()) / math.log(len(probabilities))))

    def predict(
        self,
        image_bytes: bytes,
        model_specs: Sequence[ActiveModelSpec],
        mode: InferenceMode,
    ) -> dict[str, Any]:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        tensor = self.transform(image).unsqueeze(0).to(self.device)
        ordered_specs = list(model_specs)

        if settings.PARALLEL_MODEL_INFERENCE and len(ordered_specs) > 1:
            results: list[dict[str, Any]] = []
            futures = {
                self._model_executor.submit(
                    self._safe_predict_one, tensor, spec, order
                ): order
                for order, spec in enumerate(ordered_specs, start=1)
            }
            for future in as_completed(futures):
                results.append(future.result())
            results.sort(key=lambda item: item["execution_order"])
        else:
            results = [
                self._safe_predict_one(tensor, spec, order)
                for order, spec in enumerate(ordered_specs, start=1)
            ]

        successful = [item for item in results if item["error_code"] is None]
        if not ordered_specs:
            raise ModelConfigurationError("Cần ít nhất một model được chọn")
        # Explicit single selection in an Advanced tier is not degraded ensemble.
        minimum = min(2 if mode == "advanced" else 1, len(ordered_specs))
        if len(successful) < minimum:
            raise ModelConfigurationError(
                f"Mode {mode} cần ít nhất {minimum} model chạy thành công"
            )
        canonical_classes = successful[0]["classes"]
        if any(item["classes"] != canonical_classes for item in successful[1:]):
            raise ModelConfigurationError("Thứ tự classes giữa active models không khớp")

        probability_tensors = [torch.tensor(item["all_probs"]) for item in successful]
        ensemble = torch.stack(probability_tensors).mean(dim=0)
        topk_conf, topk_idx = torch.topk(ensemble, k=min(3, len(canonical_classes)))
        confidence = float(topk_conf[0])
        margin = confidence - (float(topk_conf[1]) if len(topk_conf) > 1 else 0.0)
        entropy = float(
            -(ensemble * torch.log(ensemble.clamp_min(1e-12))).sum()
        ) / math.log(len(ensemble))
        js_divergence = self._js_divergence(probability_tensors)
        candidate_label = canonical_classes[int(topk_idx[0])]
        top_k = [
            {
                "label": canonical_classes[int(idx)],
                "confidence": round(float(conf), 6),
                "rank": rank,
            }
            for rank, (conf, idx) in enumerate(zip(topk_conf, topk_idx), start=1)
        ]

        checks = [
            {"rule": "confidence_below_threshold", "value": confidence,
             "threshold": settings.CONFIDENCE_THRESHOLD, "comparison": ">=",
             "passed": confidence >= settings.CONFIDENCE_THRESHOLD},
            {"rule": "top1_top2_margin_too_small", "value": margin,
             "threshold": settings.TOP1_MARGIN_THRESHOLD, "comparison": ">=",
             "passed": margin >= settings.TOP1_MARGIN_THRESHOLD},
            {"rule": "model_disagreement_too_high", "value": js_divergence,
             "threshold": settings.JS_DIVERGENCE_THRESHOLD, "comparison": "<=",
             "passed": js_divergence <= settings.JS_DIVERGENCE_THRESHOLD},
        ]
        failed_rules = [check["rule"] for check in checks if not check["passed"]]
        rejection_reason = failed_rules[0] if failed_rules else None
        validation_status = ("accepted" if not failed_rules else
                             "low_confidence" if rejection_reason == "confidence_below_threshold" else "ambiguous")

        agreeing = sum(item["predicted_label"] == candidate_label for item in successful)
        if len(successful) < len(ordered_specs):
            agreement_status = "degraded"
        elif len(successful) == 1:
            agreement_status = "single_model"
        elif agreeing == len(successful):
            agreement_status = "agreed"
        else:
            agreement_status = "disagreed"
        ood_score = max(1.0 - confidence, entropy, js_divergence)
        primary = next(
            (item for item in successful if item["model_type"] == "efficientnet_b0"),
            successful[0],
        )
        energy_values = [float(item["energy_score"]) for item in successful]

        # Loại tensor/list xác suất nội bộ trước khi trả response/persist.
        public_results = [
            {key: value for key, value in item.items() if key not in {"all_probs", "classes"}}
            for item in results
        ]
        return {
            "label": candidate_label if validation_status == "accepted" else None,
            "candidate_label": candidate_label,
            "confidence": round(confidence, 6),
            "is_valid_leaf": validation_status == "accepted",
            "top_k": top_k,
            "model_version": primary["version_name"],
            "primary_model_version_id": primary["model_version_id"],
            "inference_mode": mode,
            "validation_status": validation_status,
            "rejection_reason": rejection_reason,
            "agreement_status": agreement_status,
            "agreement_count": agreeing,
            "models_requested": len(ordered_specs),
            "models_succeeded": len(successful),
            "top1_top2_margin": round(margin, 6),
            "ensemble_entropy": round(entropy, 6),
            "js_divergence": round(js_divergence, 6),
            "energy_score": round(sum(energy_values) / len(energy_values), 6),
            "ood_score": round(ood_score, 6),
            "policy_version": POLICY_VERSION,
            "decision_details": {"checks": checks, "failed_rules": failed_rules,
                                 "aggregation": "mean_calibrated_probabilities",
                                 "js_normalization": "log(number_of_successful_models)",
                                 "effective_model_types": [item["model_type"] for item in successful]},
            "model_results": public_results,
        }

    def predict_bounded(
        self,
        image_bytes: bytes,
        model_specs: Sequence[ActiveModelSpec],
        mode: InferenceMode,
    ) -> dict[str, Any]:
        """Chạy inference trong slot giới hạn và chỉ nhả slot khi thật sự xong.

        Khi request HTTP timeout, worker có thể vẫn đang chạy. ``finally`` này
        giữ slot cho đến khi worker kết thúc, tránh request mới chồng thêm tải.
        """
        if not self._capacity.acquire(blocking=False):
            raise InferenceCapacityError("Hệ thống đang xử lý một lượt chẩn đoán khác")
        try:
            return self.predict(image_bytes, model_specs, mode)
        finally:
            self._capacity.release()


predict_service = PredictService()
