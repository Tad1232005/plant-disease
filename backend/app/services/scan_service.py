"""Business logic cho Scan API theo quyền sở hữu."""

from typing import Any
import json
import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.crud import disease_info as disease_crud
from app.crud import scan as scan_crud
from app.models.scan import Scan
from app.models.user import User
from app.services.image_storage_service import delete_stored_image

logger = logging.getLogger(__name__)


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
    if scan.is_valid_leaf and scan.predicted_label is not None:
        disease = disease_crud.get_disease_info_by_label(
            db,
            scan.predicted_label,
            include_inactive=True,
        )

    return {
        "id": scan.id,
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
    db.delete(scan)
    db.commit()
    try:
        delete_stored_image(image_path)
    except OSError:
        logger.exception("Không thể dọn file của scan_id=%s", scan_id)
