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
from typing import Any, Literal, Sequence, cast
import logging
from collections import OrderedDict

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from sqlalchemy.orm import Session
from torchvision import models, transforms

from app.core.config import BASE_DIR, Settings, settings
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


def get_active_models(
    db: Session,
    mode: InferenceMode,
    model_type: str | None = None,
    primary_model: str | None = None,
) -> list[ActiveModelSpec]:
    """Lấy đúng active version của từng model type theo thứ tự policy hoặc primary_model chỉ định."""
    if model_type is not None:
        if model_type not in MODEL_TYPES_BY_MODE[mode]:
            raise ModeNotAllowedError(f"Mode {mode} không được dùng model {model_type}")
        required = (model_type,)
    else:
        tier_models = list(MODEL_TYPES_BY_MODE[mode])
        if primary_model is not None:
            if primary_model not in tier_models:
                raise ModeNotAllowedError(f"Primary model '{primary_model}' không thuộc mode '{mode}'")
            tier_models.remove(primary_model)
            required = tuple([primary_model] + tier_models)
        else:
            required = tuple(tier_models)
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
    missing = [m_type for m_type in required if m_type not in by_type]
    if missing:
        raise ModelConfigurationError(
            "Thiếu active model version: " + ", ".join(missing)
        )
    invalid = [
        m_type
        for m_type in required
        if not by_type[m_type].classes_path
        or not by_type[m_type].sha256
        or len(by_type[m_type].sha256 or "") != 64
    ]
    if invalid:
        raise ModelConfigurationError(
            "Active model thiếu classes/checksum: " + ", ".join(invalid)
        )
    return [
        ActiveModelSpec(
            id=by_type[m_type].id,
            version_name=by_type[m_type].version_name,
            model_type=m_type,
            file_path=by_type[m_type].file_path,
            classes_path=by_type[m_type].classes_path or "",
            temperature=by_type[m_type].temperature,
            sha256=by_type[m_type].sha256,
        )
        for m_type in required
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
        if settings.MAX_CONCURRENT_GRADCAM < 1:
            raise ValueError("MAX_CONCURRENT_GRADCAM phải lớn hơn hoặc bằng 1")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._cache: OrderedDict[ActiveModelSpec, LoadedModel] = OrderedDict()
        self._load_lock = Lock()
        # Backpropagation for Grad-CAM mutates gradients on a shared cached model.
        # It must never overlap another Grad-CAM or ordinary inference on that model.
        self._explain_lock = Lock()
        # Separate capacity slots: inference and Grad-CAM do not compete.
        self._capacity = BoundedSemaphore(settings.MAX_CONCURRENT_INFERENCES)
        self._gradcam_capacity = BoundedSemaphore(settings.MAX_CONCURRENT_GRADCAM)
        # Dùng chung executor giữa các request để không tạo 2-3 thread mới
        # cho mỗi lần gọi Standard/Advanced.
        self._model_executor = ThreadPoolExecutor(
            max_workers=settings.INFERENCE_THREAD_WORKERS,
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
        self._ood_config = self._load_ood_config()
        self._calibrated_js_thresholds = self._load_calibrated_thresholds()


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
            while len(self._cache) > settings.MODEL_CACHE_SIZE:
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

    @classmethod
    def _load_ood_config(cls) -> dict[str, Any]:
        """Đọc toàn bộ file ood_threshold.json."""
        candidate_paths = [
            Path(settings.MODEL_ARTIFACT_ROOT) / "ood_threshold.json",
            BASE_DIR / "app" / "ml_assets" / "models" / "ood_threshold.json",
            BASE_DIR / "app" / "ml_assets" / "ood_threshold.json",
            BASE_DIR.parent / "ml" / "outputs" / "ood_threshold.json",
        ]
        for candidate in candidate_paths:
            if candidate.is_file():
                try:
                    with candidate.open("r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception as exc:
                    logger.warning("Failed to load OOD config from %s: %s", candidate, exc)
        return {}

    @classmethod
    def _load_calibrated_thresholds(cls) -> dict[str, float]:
        """Đọc và chuẩn hóa ngưỡng ensemble disagreement từ ood_threshold.json theo từng tier."""
        candidate_paths = [
            Path(settings.MODEL_ARTIFACT_ROOT) / "ood_threshold.json",
            BASE_DIR / "app" / "ml_assets" / "models" / "ood_threshold.json",
            BASE_DIR / "app" / "ml_assets" / "ood_threshold.json",
            BASE_DIR.parent / "ml" / "outputs" / "ood_threshold.json",
        ]
        thresholds: dict[str, float] = {}
        for candidate in candidate_paths:
            if candidate.is_file():
                try:
                    with candidate.open("r", encoding="utf-8") as f:
                        data = json.load(f)
                    tiers = data.get("tiers", {})
                    for tier_name, tier_info in tiers.items():
                        models_list = tier_info.get("models", [])
                        n_models = len(models_list)
                        sig = tier_info.get("signals", {}).get("ensemble_disagreement", {})
                        raw_th = sig.get("threshold")
                        if raw_th is not None and n_models > 1 and math.log(n_models) > 0:
                            norm_th = min(1.0, max(0.0, float(raw_th) / math.log(n_models)))
                            thresholds[tier_name] = round(norm_th, 6)
                    if thresholds:
                        logger.info("Loaded calibrated OOD disagreement thresholds from %s: %s", candidate, thresholds)
                        return thresholds
                except Exception as exc:
                    logger.warning("Failed to load OOD thresholds from %s: %s", candidate, exc)
        return thresholds

    def get_js_divergence_threshold(self, mode: InferenceMode, num_models: int) -> float:
        """Lấy ngưỡng JS divergence: ưu tiên override từ settings nếu khác default, sau đó đến calibrated tier threshold."""
        default_val = float(Settings.model_fields["JS_DIVERGENCE_THRESHOLD"].default)
        current_val = float(settings.JS_DIVERGENCE_THRESHOLD)
        # Dùng math.isclose thay vì != để tránh false-positive với float repr
        if not math.isclose(current_val, default_val, rel_tol=1e-9, abs_tol=1e-12):
            return current_val
        if num_models > 1 and mode in self._calibrated_js_thresholds:
            return self._calibrated_js_thresholds[mode]
        return current_val

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
        if not ordered_specs:
            raise ModelConfigurationError("Cần ít nhất một model được chọn")

        # TẦNG 1: Chạy Primary model (model đầu tiên trong ordered_specs)
        primary_spec = ordered_specs[0]
        primary_res = self._safe_predict_one(tensor, primary_spec, 1)

        # Lấy ngưỡng OOD từ ood_threshold.json theo tier
        tier_data = self._ood_config.get("tiers", {}).get(mode, {})
        gates = tier_data.get("gates", {})
        high_conf_msp = float(gates.get("high_conf_msp", self._ood_config.get("high_conf_msp", 0.9852286577224731)))
        low_conf_msp = float(gates.get("low_conf_msp", self._ood_config.get("low_conf_msp", 0.5084525406360626)))
        signals = tier_data.get("signals", {})
        msp_threshold = float(signals.get("msp", {}).get("threshold", 0.9334873557090759))
        js_threshold = self.get_js_divergence_threshold(mode, len(ordered_specs))

        run_stage_2 = False
        stage_1_early_exit = False
        stage_1_rejected = False

        if len(ordered_specs) > 1 and primary_res["error_code"] is None:
            # Calibrated MSP của primary model ở Tầng 1
            msp = float(primary_res["confidence"])
            margin = float(primary_res["top1_top2_margin"] or 0.0)

            if msp >= high_conf_msp and margin >= settings.TOP1_MARGIN_THRESHOLD:
                # Tầng 1: Model rất tự tin -> chốt luôn kết quả, không chạy Tầng 2
                stage_1_early_exit = True
            elif msp < low_conf_msp:
                # Tầng 1: Quá phân vân -> loại luôn
                stage_1_rejected = True
            else:
                # Rơi vào vùng phân vân (low <= msp < high) -> kích hoạt Tầng 2
                run_stage_2 = True
        elif len(ordered_specs) > 1 and primary_res["error_code"] is not None:
            # Primary model bị lỗi -> kích hoạt các model phụ (degraded)
            run_stage_2 = True

        if run_stage_2:
            aux_specs = ordered_specs[1:]
            if settings.PARALLEL_MODEL_INFERENCE and len(aux_specs) > 1:
                aux_results: list[dict[str, Any]] = []
                futures = {
                    self._model_executor.submit(
                        self._safe_predict_one, tensor, spec, order
                    ): order
                    for order, spec in enumerate(aux_specs, start=2)
                }
                for future in as_completed(futures):
                    aux_results.append(future.result())
                aux_results.sort(key=lambda item: item["execution_order"])
            else:
                aux_results = [
                    self._safe_predict_one(tensor, spec, order)
                    for order, spec in enumerate(aux_specs, start=2)
                ]
            results = [primary_res] + aux_results
        else:
            results = [primary_res]

        successful = [item for item in results if item["error_code"] is None]
        if not successful:
            raise ModelConfigurationError("Tất cả model đều inference thất bại")

        # Xử lý khi chỉ dừng ở Tầng 1 (hoặc Single model, hoặc Tầng 1 early-exit/reject)
        if not run_stage_2:
            primary = successful[0]
            confidence = float(primary["confidence"])
            margin = float(primary["top1_top2_margin"] or 0.0)
            candidate_label = primary["predicted_label"]
            entropy = float(primary["entropy"])
            energy_score = float(primary["energy_score"])
            ood_score = min(1.0, 0.4 * (1.0 - confidence) + 0.3 * entropy)

            if stage_1_early_exit:
                validation_status = "accepted"
                rejection_reason = None
                ood_method = "high_confidence"
                checks = [
                    {"rule": "confidence_below_threshold", "value": confidence,
                     "threshold": high_conf_msp, "comparison": ">=", "passed": True},
                    {"rule": "top1_top2_margin_too_small", "value": margin,
                     "threshold": settings.TOP1_MARGIN_THRESHOLD, "comparison": ">=", "passed": True},
                ]
                failed_rules: list[str] = []
            elif stage_1_rejected:
                validation_status = "low_confidence"
                rejection_reason = "confidence_below_threshold"
                ood_method = "low_confidence"
                checks = [
                    {"rule": "confidence_below_threshold", "value": confidence,
                     "threshold": low_conf_msp, "comparison": ">=", "passed": False},
                ]
                failed_rules = ["confidence_below_threshold"]
            else:
                # len(ordered_specs) == 1 (chế độ single hoặc mode basic)
                min_conf = settings.CONFIDENCE_THRESHOLD
                checks = [
                    {"rule": "confidence_below_threshold", "value": confidence,
                     "threshold": min_conf, "comparison": ">=",
                     "passed": confidence >= min_conf},
                    {"rule": "top1_top2_margin_too_small", "value": margin,
                     "threshold": settings.TOP1_MARGIN_THRESHOLD, "comparison": ">=",
                     "passed": margin >= settings.TOP1_MARGIN_THRESHOLD},
                ]
                failed_rules = [check["rule"] for check in checks if not check["passed"]]
                rejection_reason = failed_rules[0] if failed_rules else None
                validation_status = "accepted" if not failed_rules else "low_confidence"
                ood_method = "single_model"

            public_results = [
                {key: value for key, value in item.items() if key not in {"all_probs", "classes"}}
                for item in results
            ]
            return {
                "label": candidate_label if validation_status == "accepted" else None,
                "candidate_label": candidate_label,
                "confidence": round(confidence, 6),
                "is_valid_leaf": validation_status == "accepted",
                "top_k": primary["top_k"],
                "model_version": primary["version_name"],
                "primary_model_version_id": primary["model_version_id"],
                "inference_mode": mode,
                "validation_status": validation_status,
                "rejection_reason": rejection_reason,
                "agreement_status": "single_model",
                "agreement_count": 1,
                "models_requested": len(ordered_specs),
                "models_succeeded": 1,
                "top1_top2_margin": round(margin, 6),
                "ensemble_entropy": round(entropy, 6),
                "js_divergence": 0.0,
                "energy_score": round(energy_score, 6),
                "ood_score": round(ood_score, 6),
                "policy_version": POLICY_VERSION,
                "decision_details": {
                    "stage_reached": 1,
                    "ood_method": ood_method,
                    "primary_model": primary["model_type"],
                    "msp_calibrated": round(confidence, 6),
                    "high_conf_msp_threshold": high_conf_msp,
                    "low_conf_msp_threshold": low_conf_msp,
                    "checks": checks,
                    "failed_rules": failed_rules,
                    "effective_model_types": [primary["model_type"]],
                },
                "model_results": public_results,
            }

        # Đã chạy Tầng 2: Soft-voting Ensemble
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
             "threshold": js_threshold, "comparison": "<=",
             "passed": js_divergence <= js_threshold},
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

        ood_score = min(1.0, 0.4 * (1.0 - confidence) + 0.3 * entropy + 0.3 * js_divergence)
        primary = next(
            (item for item in successful if item["model_type"] == primary_spec.model_type),
            successful[0],
        )
        energy_values = [float(item["energy_score"]) for item in successful]

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
            "decision_details": {
                "stage_reached": 2,
                "ood_method": "ensemble",
                "primary_model": primary_spec.model_type,
                "msp_calibrated": round(primary_res.get("confidence") or 0.0, 6) if primary_res["error_code"] is None else None,
                "high_conf_msp_threshold": high_conf_msp,
                "low_conf_msp_threshold": low_conf_msp,
                "disagreement_threshold": js_threshold,
                "checks": checks,
                "failed_rules": failed_rules,
                "aggregation": "mean_calibrated_probabilities",
                "js_normalization": "log(number_of_successful_models)",
                "effective_model_types": [item["model_type"] for item in successful],
            },
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

    @staticmethod
    def _gradcam_target_layer(model: nn.Module, model_type: str) -> nn.Module:
        """Return the final convolutional block for a supported backbone."""
        from app.services.gradcam_service import get_gradcam_target_layer
        return get_gradcam_target_layer(model, model_type)

    def generate_gradcam(
        self,
        image_bytes: bytes,
        spec: ActiveModelSpec,
        target_label: str,
    ) -> bytes:
        """Render a PNG Grad-CAM overlay for one persisted model prediction.

        This uses the exact cached model bundle and preprocessing policy used by
        inference.  The returned visualization is explanatory only; callers must
        not treat it as evidence that a prediction is correct.

        Uses a dedicated _gradcam_capacity slot so Grad-CAM requests cannot
        consume the inference semaphore and stall real-time diagnosis.
        """
        if not self._gradcam_capacity.acquire(blocking=False):
            raise InferenceCapacityError("Hệ thống đang xử lý một lượt Grad-CAM khác")
        try:
            with self._explain_lock:
                loaded = self._load(spec)
                image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
                from app.services.gradcam_service import compute_gradcam_overlay
                return compute_gradcam_overlay(
                    model=loaded.model,
                    classes=loaded.classes,
                    image=image,
                    target_label=target_label,
                    device=self.device,
                    transform=self.transform,
                    model_type=spec.model_type,
                )
        finally:
            self._gradcam_capacity.release()


predict_service = PredictService()
