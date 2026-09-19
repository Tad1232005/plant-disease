"""Khám phá và kiểm tra contract của bundle model do nhóm ML bàn giao."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any


SUPPORTED_MODEL_TYPES = ("efficientnet_b0", "mobilenet_v2", "resnet50")


@dataclass(frozen=True)
class ModelArtifactSpec:
    version_name: str
    model_type: str
    task: str
    file_path: str
    classes_path: str
    temperature_path: str
    temperature: float
    sha256: str
    classes: tuple[str, ...]


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"Thiếu artifact bắt buộc: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Artifact JSON không hợp lệ: {path}") from exc


def _bundle_digest(paths: list[Path]) -> str:
    """Hash bundle ổn định giữa LF/CRLF và cách format JSON."""
    digest = hashlib.sha256()
    digest.update(b"plant-disease-bundle-v2\0")
    for path in paths:
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        try:
            if path.suffix.lower() == ".json":
                value = json.loads(path.read_text(encoding="utf-8"))
                canonical = json.dumps(
                    value,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
                digest.update(canonical)
            else:
                with path.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(chunk)
        except FileNotFoundError as exc:
            raise RuntimeError(f"Thiếu artifact bắt buộc: {path}") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Artifact JSON không hợp lệ: {path}") from exc
        digest.update(b"\0")
    return digest.hexdigest()


def load_artifact(manifest_path: str | Path) -> ModelArtifactSpec:
    """Đọc một manifest và xác minh các file liên quan khớp nhau."""
    manifest_file = Path(manifest_path).resolve()
    manifest = _read_json(manifest_file)
    if not isinstance(manifest, dict):
        raise RuntimeError(f"Manifest phải là JSON object: {manifest_file}")

    required = {
        "version_name", "model_type", "task", "num_classes", "input_size",
        "weights", "classes", "model_type_file", "temperature_file", "output",
    }
    missing = sorted(required - manifest.keys())
    if missing:
        raise RuntimeError(f"Manifest thiếu field: {', '.join(missing)}")
    model_type = str(manifest["model_type"])
    if model_type not in SUPPORTED_MODEL_TYPES:
        raise RuntimeError(f"model_type chưa được backend hỗ trợ: {model_type}")
    if manifest["task"] != "disease_classification":
        raise RuntimeError("Artifact không phải task disease_classification")
    if manifest["output"] != "logits":
        raise RuntimeError("Backend cần model trả logits để temperature scaling")
    if manifest["input_size"] != [224, 224]:
        raise RuntimeError("Backend hiện chỉ hỗ trợ input_size [224, 224]")

    root = manifest_file.parent
    weights_path = root / str(manifest["weights"])
    classes_path = root / str(manifest["classes"])
    model_type_path = root / str(manifest["model_type_file"])
    temperature_path = root / str(manifest["temperature_file"])
    if any(not path.resolve().is_relative_to(root) for path in
           (weights_path, classes_path, model_type_path, temperature_path)):
        raise RuntimeError("Artifact không được nằm ngoài thư mục bundle")
    classes_raw = _read_json(classes_path)
    type_raw = _read_json(model_type_path)
    temperature_raw = _read_json(temperature_path)

    if not isinstance(classes_raw, list) or not classes_raw:
        raise RuntimeError(f"classes phải là list không rỗng: {classes_path}")
    if any(not isinstance(label, str) or not label or len(label) > 50 for label in classes_raw):
        raise RuntimeError(f"classes chứa label không hợp lệ: {classes_path}")
    if len(classes_raw) != len(set(classes_raw)):
        raise RuntimeError(f"classes chứa label trùng: {classes_path}")
    if len(classes_raw) != int(manifest["num_classes"]):
        raise RuntimeError("num_classes trong manifest không khớp classes.json")
    if not isinstance(type_raw, dict) or type_raw.get("model_type") != model_type:
        raise RuntimeError("model_type.json không khớp manifest")
    if not isinstance(temperature_raw, dict):
        raise RuntimeError("temperature.json phải là JSON object")
    temperature = float(temperature_raw.get("temperature", 0))
    if not math.isfinite(temperature) or temperature <= 0:
        raise RuntimeError("temperature phải lớn hơn 0")
    if int(temperature_raw.get("num_classes", -1)) != len(classes_raw):
        raise RuntimeError("num_classes trong temperature.json không khớp classes")

    paths = [weights_path, classes_path, model_type_path, temperature_path, manifest_file]
    digest = _bundle_digest(paths)
    return ModelArtifactSpec(
        version_name=str(manifest["version_name"]),
        model_type=model_type,
        task=str(manifest["task"]),
        file_path=str(weights_path.resolve()),
        classes_path=str(classes_path.resolve()),
        temperature_path=str(temperature_path.resolve()),
        temperature=temperature,
        sha256=digest,
        classes=tuple(classes_raw),
    )


def discover_artifacts(root: str | Path) -> list[ModelArtifactSpec]:
    """Nạp đúng ba bundle và yêu cầu thứ tự class giống tuyệt đối."""
    root_path = Path(root).resolve()
    specs = [load_artifact(path) for path in sorted(root_path.glob("*/manifest.json"))]
    found = {item.model_type for item in specs}
    expected = set(SUPPORTED_MODEL_TYPES)
    if found != expected or len(specs) != len(expected):
        raise RuntimeError(
            "MODEL_ARTIFACT_ROOT phải chứa đúng một bundle cho mỗi model_type: "
            + ", ".join(SUPPORTED_MODEL_TYPES)
        )
    canonical = specs[0].classes
    if any(item.classes != canonical for item in specs[1:]):
        raise RuntimeError("Thứ tự classes của ba model không giống nhau")
    return specs
