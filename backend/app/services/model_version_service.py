"""Đăng ký và activate Model Version với validate + warm-up + transaction.

Quy tắc khi activate:
- Kiểm tra manifest/checksum, file tồn tại và load được.
- Kiểm tra số output khớp classes.json.
- Warm-up inference (forward pass một tensor ngẫu nhiên).
- Activate version mới và deactivate version cũ cùng model_type trong một
  transaction; ba model_type có thể active song song.
- Rollback nếu load hoặc warm-up thất bại; cache predict_service được invalidate
  bằng cách cache sẽ miss khi sha256 mới không khớp key cũ.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING

import torch

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from app.services.predict_service import ActiveModelSpec

from app.models.model_version import ModelVersion
from app.schemas.model_version import RegisterModelVersionRequest
from app.services.model_artifact_service import load_artifact, SUPPORTED_MODEL_TYPES

logger = logging.getLogger(__name__)


def list_model_versions(
    db: Session,
    *,
    model_type: str | None = None,
    is_active: bool | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[ModelVersion]:
    """Liệt kê Model Version, có thể lọc theo model_type và trạng thái."""
    query = db.query(ModelVersion)
    if model_type is not None:
        if model_type not in SUPPORTED_MODEL_TYPES:
            raise HTTPException(status_code=422, detail=f"model_type không hợp lệ: {model_type}")
        query = query.filter(ModelVersion.model_type == model_type)
    if is_active is not None:
        query = query.filter(ModelVersion.is_active.is_(is_active))
    return query.order_by(ModelVersion.model_type, ModelVersion.created_at.desc(), ModelVersion.id.desc()).offset(offset).limit(limit).all()


def get_model_version(db: Session, version_id: int) -> ModelVersion:
    """Lấy chi tiết một Model Version; 404 nếu không tồn tại."""
    version = db.get(ModelVersion, version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy Model Version")
    return version


def register_version(
    db: Session,
    data: RegisterModelVersionRequest,
) -> ModelVersion:
    """Đọc manifest, kiểm tra contract, rồi đăng ký vào DB.

    Không activate ngay; Admin phải gọi activate riêng sau khi xác nhận.
    """
    manifest_path = Path(data.manifest_path)
    if not manifest_path.is_absolute():
        raise HTTPException(
            status_code=422,
            detail="manifest_path phải là đường dẫn tuyệt đối trên server",
        )
    try:
        spec = load_artifact(manifest_path)
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=f"Artifact không hợp lệ: {exc}") from exc

    # Chặn trùng version_name
    existing = db.query(ModelVersion).filter(ModelVersion.version_name == spec.version_name).first()
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=f"version_name '{spec.version_name}' đã được đăng ký (id={existing.id})",
        )

    version = ModelVersion(
        version_name=spec.version_name,
        model_type=spec.model_type,
        task=spec.task,
        file_path=spec.file_path,
        classes_path=spec.classes_path,
        temperature_path=spec.temperature_path,
        temperature=spec.temperature,
        sha256=spec.sha256,
        is_active=False,
        is_enabled=True,
        accuracy=data.accuracy,
        macro_f1=data.macro_f1,
        ece=data.ece,
        metrics_path=data.metrics_path,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    logger.info(
        "Đã đăng ký ModelVersion id=%s version_name=%s model_type=%s",
        version.id, version.version_name, version.model_type,
    )
    return version


def activate_version(db: Session, version_id: int) -> tuple[ModelVersion, ModelVersion | None, float]:
    """Validate + warm-up + activate trong một transaction.

    Trả về (activated_version, deactivated_version | None, warmup_latency_ms).
    Rollback toàn bộ nếu load hoặc warm-up thất bại.
    """
    # Import ở đây để tránh circular import với predict_service sử dụng ModelVersion
    from app.services.predict_service import predict_service, ActiveModelSpec, ModelConfigurationError, InferenceCapacityError

    version = db.execute(
        select(ModelVersion).where(ModelVersion.id == version_id).with_for_update()
    ).scalar_one_or_none()
    if version is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy Model Version")
    if version.is_active:
        # Idempotent — already active
        return version, None, 0.0
    if not version.is_enabled:
        raise HTTPException(status_code=409, detail="Model Version bị disabled, không thể activate")
    if not version.sha256 or len(version.sha256) != 64:
        raise HTTPException(status_code=409, detail="Model Version thiếu checksum sha256 hợp lệ")
    if not version.classes_path:
        raise HTTPException(status_code=409, detail="Model Version thiếu classes_path")

    # Validate artifact còn đúng trên disk
    try:
        manifest_path = Path(version.file_path).parent / "manifest.json"
        spec_on_disk = load_artifact(manifest_path)
        if spec_on_disk.sha256 != version.sha256:
            raise HTTPException(
                status_code=409,
                detail="Checksum artifact trên disk không khớp record DB; bundle có thể đã bị thay thế",
            )
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=f"Artifact không hợp lệ: {exc}") from exc

    # Warm-up inference — dùng tensor ngẫu nhiên, không cần DB session
    active_spec = ActiveModelSpec(
        id=version.id,
        version_name=version.version_name,
        model_type=version.model_type,
        file_path=version.file_path,
        classes_path=version.classes_path,
        temperature=version.temperature,
        sha256=version.sha256,
    )
    try:
        t0 = time.perf_counter()
        _warmup_model(predict_service, active_spec)
        warmup_ms = (time.perf_counter() - t0) * 1000
    except ModelConfigurationError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Warm-up thất bại, không thể activate: {exc}",
        ) from exc
    except InferenceCapacityError as exc:
        raise HTTPException(
            status_code=503,
            detail="Hệ thống đang bận inference, vui lòng thử lại sau.",
        ) from exc

    # Transaction: deactivate old, activate new
    old_version: ModelVersion | None = db.execute(
        select(ModelVersion)
        .where(
            ModelVersion.model_type == version.model_type,
            ModelVersion.is_active.is_(True),
            ModelVersion.id != version.id,
        )
        .with_for_update()
    ).scalar_one_or_none()

    if old_version is not None:
        old_version.is_active = False

    version.is_active = True
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(version)
    if old_version is not None:
        db.refresh(old_version)

    logger.info(
        "Activated ModelVersion id=%s version_name=%s; deactivated id=%s; warmup=%.1fms",
        version.id, version.version_name,
        old_version.id if old_version else None,
        warmup_ms,
    )
    return version, old_version, warmup_ms


def _warmup_model(service, spec: "ActiveModelSpec") -> None:
    """Chạy forward pass một tensor ngẫu nhiên để xác nhận model load được."""
    import io
    import numpy as np
    from PIL import Image as PILImage

    # Tạo ảnh RGB ngẫu nhiên 224×224
    rng = np.random.default_rng(seed=42)
    arr = rng.integers(0, 256, (224, 224, 3), dtype=np.uint8)
    img = PILImage.fromarray(arr, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    image_bytes = buf.getvalue()

    # Dùng internal _load để verify model load strict; không đi qua bounded semaphore
    loaded = service._load(spec)
    tensor = service.transform(img).unsqueeze(0).to(service.device)
    with torch.no_grad():
        logits = loaded.model(tensor)
    if not torch.isfinite(logits).all():
        from app.services.predict_service import ModelConfigurationError
        raise ModelConfigurationError("Warm-up logits chứa NaN/Inf")
    _ = image_bytes  # referenced to avoid unused warning
