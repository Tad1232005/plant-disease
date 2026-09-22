"""Business logic cho Scan API theo quyền sở hữu."""

from typing import Any
from pathlib import Path
import json
import logging
import os
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud import disease_info as disease_crud
from app.crud import scan as scan_crud
from app.models.model_version import ModelVersion
from app.models.scan import Scan
from app.models.user import User
from app.services.image_storage_service import delete_stored_image, resolve_stored_image
from app.services.predict_service import (
    ActiveModelSpec,
    InferenceCapacityError,
    ModelConfigurationError,
    predict_service,
)

logger = logging.getLogger(__name__)


def get_scan_image(db: Session, current_user: User, scan_id: int) -> Path:
    scan = _get_owned_scan(db, current_user, scan_id)
    path = resolve_stored_image(scan.image_path)
    if path is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy ảnh scan")
    return path


def get_scan_gradcam(db: Session, current_user: User, scan_id: int) -> Path:
    """Return an existing private Grad-CAM image for the scan owner."""
    scan = _get_owned_scan(db, current_user, scan_id)
    if not scan.gradcam_path:
        raise HTTPException(status_code=404, detail="Scan chưa có Grad-CAM")
    path = resolve_stored_image(scan.gradcam_path)
    if path is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy ảnh Grad-CAM")
    return path


def _scan_model_spec(scan: Scan) -> ActiveModelSpec:
    version: ModelVersion | None = scan.primary_model_version
    if version is None and scan.primary_model_version_id is not None:
        # The relationship is normally loaded; this branch makes legacy session
        # behavior explicit rather than silently picking an active model.
        raise ModelConfigurationError("Không tải được model version đã lưu của Scan")
    if version is None:
        raise ModelConfigurationError("Scan cũ không có model version để tạo Grad-CAM")
    if not version.classes_path or not version.sha256 or len(version.sha256) != 64:
        raise ModelConfigurationError("Model version của Scan thiếu metadata artifact")
    return ActiveModelSpec(
        id=version.id,
        version_name=version.version_name,
        model_type=version.model_type,
        file_path=version.file_path,
        classes_path=version.classes_path,
        temperature=version.temperature,
        sha256=version.sha256,
    )


def create_scan_gradcam(db: Session, current_user: User, scan_id: int) -> str:
    """Create a private Grad-CAM once for an accepted, owned Scan.

    The artifact is derived from the model version recorded on the Scan, never
    whichever version happens to be active today.  It remains an explanation,
    not a second diagnosis or a botanical leaf detector.
    """
    scan = _get_owned_scan(db, current_user, scan_id)
    if scan.validation_status != "accepted" or not scan.predicted_label:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Chỉ Scan được chấp nhận mới có thể tạo Grad-CAM.",
        )
    if scan.gradcam_path and resolve_stored_image(scan.gradcam_path) is not None:
        return scan.gradcam_path
    image_path = resolve_stored_image(scan.image_path)
    if image_path is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy ảnh scan")
    try:
        content = predict_service.generate_gradcam(
            image_path.read_bytes(),
            _scan_model_spec(scan),
            scan.predicted_label,
        )
    except InferenceCapacityError as exc:
        raise HTTPException(status_code=503, detail="Hệ thống đang bận tạo Grad-CAM, vui lòng thử lại.") from exc
    except ModelConfigurationError as exc:
        logger.exception("Không thể tạo Grad-CAM cho scan_id=%s", scan.id)
        raise HTTPException(status_code=503, detail="Model không thể tạo Grad-CAM cho Scan này.") from exc
    except (OSError, ValueError) as exc:
        logger.exception("Không thể đọc/tạo Grad-CAM cho scan_id=%s", scan.id)
        raise HTTPException(status_code=503, detail="Không thể tạo ảnh Grad-CAM.") from exc

    upload_dir = Path(settings.UPLOAD_DIR).resolve()
    gradcam_dir = upload_dir / "gradcam"
    gradcam_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}.png"
    target = gradcam_dir / filename
    temporary = target.with_suffix(".png.tmp")
    try:
        temporary.write_bytes(content)
        os.replace(temporary, target)
        old_path = scan.gradcam_path
        scan.gradcam_path = f"storage/uploads/gradcam/{filename}"
        db.commit()
    except Exception:
        db.rollback()
        target.unlink(missing_ok=True)
        raise
    finally:
        temporary.unlink(missing_ok=True)
    if old_path and old_path != scan.gradcam_path:
        try:
            delete_stored_image(old_path)
        except OSError:
            logger.exception("Không thể dọn Grad-CAM cũ cho scan_id=%s", scan.id)
    return scan.gradcam_path


def _parse_topk(raw_value: str | None, *, scan_id: int) -> list[dict[str, Any]]:
    """Không để JSON audit cũ/hỏng làm hỏng toàn bộ Scan detail."""
    if not raw_value:
        return []
    try:
        parsed = json.loads(raw_value)
    except (json.JSONDecodeError, TypeError):
        logger.warning("topk_json không hợp lệ cho scan_id=%s", scan_id)
        return []
    if not isinstance(parsed, list):
        logger.warning("topk_json không phải list cho scan_id=%s", scan_id)
        return []
    return [item for item in parsed if isinstance(item, dict)]


def list_history(
    db: Session,
    current_user: User,
    *,
    limit: int,
    offset: int,
) -> list[Scan]:
    """Mọi tài khoản đã đăng nhập chỉ thấy scan của chính mình."""
    return scan_crud.get_scans_by_user(
        db,
        current_user.id,
        limit=limit,
        offset=offset,
    )


def _get_owned_scan(db: Session, current_user: User, scan_id: int) -> Scan:
    scan = scan_crud.get_scan_by_id(db, scan_id)
    if scan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy scan",
        )
    if scan.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không sở hữu scan này",
        )
    return scan


def get_scan_detail(
    db: Session,
    current_user: User,
    scan_id: int,
) -> dict[str, Any]:
    """Trả chi tiết scan sở hữu, kèm disease info nếu có."""
    scan = _get_owned_scan(db, current_user, scan_id)
    disease = None
    if scan.validation_status == "accepted" and scan.is_valid_leaf and scan.predicted_label is not None:
        disease = disease_crud.get_disease_info_by_label(
            db,
            scan.predicted_label,
            include_inactive=True,
        )

    return {
        "id": scan.id,
        "prediction_context": scan.prediction_context,
        "user_id": scan.user_id,
        "farm_id": scan.farm_id,
        "image_path": scan.image_path,
        "predicted_label": scan.predicted_label,
        "confidence": scan.confidence,
        "is_valid_leaf": scan.is_valid_leaf,
        "gradcam_path": scan.gradcam_path,
        "model_version": scan.model_version,
        "primary_model_version_id": scan.primary_model_version_id,
        "inference_mode": scan.inference_mode,
        "validation_status": scan.validation_status,
        "rejection_reason": scan.rejection_reason,
        "agreement_status": scan.agreement_status,
        "top1_top2_margin": scan.top1_top2_margin,
        "ensemble_entropy": scan.ensemble_entropy,
        "js_divergence": scan.js_divergence,
        "energy_score": scan.energy_score,
        "ood_score": scan.ood_score,
        "policy_version": scan.policy_version,
        "created_at": scan.created_at,
        "disease_name": disease.disease_name if disease else None,
        "treatment": disease.treatment if disease else None,
        "top3": sorted(scan.topk_results, key=lambda item: item.rank),
        "model_results": [
            {
                "model_version_id": item.model_version_id,
                "version_name": item.model_version.version_name,
                "model_type": item.model_version.model_type,
                "execution_order": item.execution_order,
                "predicted_label": item.predicted_label,
                "confidence": item.confidence,
                "top1_top2_margin": item.top1_top2_margin,
                "entropy": item.entropy,
                "energy_score": item.energy_score,
                "accepted": item.accepted,
                "latency_ms": item.latency_ms,
                "error_code": item.error_code,
                "top_k": _parse_topk(item.topk_json, scan_id=scan.id),
            }
            for item in sorted(scan.model_results, key=lambda row: row.execution_order)
        ],
    }


def delete_scan(db: Session, current_user: User, scan_id: int) -> None:
    """Xóa record/top-k và dọn ảnh upload cục bộ sau khi commit DB."""
    scan = _get_owned_scan(db, current_user, scan_id)
    image_path = scan.image_path
    gradcam_path = scan.gradcam_path
    db.delete(scan)
    db.commit()
    try:
        delete_stored_image(image_path)
    except OSError:
        logger.exception("Không thể dọn file của scan_id=%s", scan_id)
    if gradcam_path:
        try:
            delete_stored_image(gradcam_path)
        except OSError:
            logger.exception("Không thể dọn Grad-CAM của scan_id=%s", scan_id)
