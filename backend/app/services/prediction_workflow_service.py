"""Điều phối inference thành Scan persisted theo optional auth và Farm RBAC."""

import json
import logging
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.crud import disease_info as disease_crud
from app.crud import farm as farm_crud
from app.crud import farm_member as member_crud
from app.models.scan import Scan
from app.models.scan_topk import ScanTopK
from app.models.scan_model_result import ScanModelResult
from app.models.user import User
from app.schemas.predict import PredictResponse
from app.services.image_storage_service import (
    ValidatedImage,
    delete_stored_image,
    save_image,
)

logger = logging.getLogger(__name__)


def _resolve_farm(
    db: Session,
    user: User,
    farm_id: int | None,
) -> tuple[int | None, str, str | None]:
    if farm_id is None:
        return None, "not_requested", None

    farm = farm_crud.get_farm_by_id(db, farm_id, for_update=True)
    allowed = False
    if farm is not None and user.role == "manager":
        allowed = farm.owner_id == user.id
    elif farm is not None and user.role == "user" and user.created_by is not None:
        allowed = farm.owner_id == user.created_by and member_crud.get_membership(
            db,
            farm_id=farm_id,
            user_id=user.id,
            for_update=True,
        ) is not None

    if allowed:
        return farm_id, "assigned", None
    return (
        None,
        "not_allowed",
        "Farm không tồn tại hoặc tài khoản không được phép gắn Scan vào Farm này.",
    )


def _disease_payload(db: Session, result: dict[str, Any]) -> dict[str, Any]:
    if result["validation_status"] != "accepted" or not result.get("label"):
        return {
            "warning": (
                "Ảnh không đủ tin cậy hoặc không khớp rõ một nhãn hiện có; "
                "không hiển thị khuyến nghị điều trị."
            ),
            "disease_name": None,
            "description": None,
            "treatment": None,
            "severity_level": None,
        }
    disease = disease_crud.get_disease_info_by_label(db, result["label"])
    return {
        "warning": "Kết quả phân loại tham khảo; hệ thống chưa xác minh ảnh là lá hoặc thuộc loài được hỗ trợ.",
        "disease_name": disease.disease_name if disease else None,
        "description": disease.description if disease else None,
        "treatment": disease.treatment if disease else None,
        "severity_level": disease.severity_level if disease else None,
    }


def complete_prediction(
    db: Session,
    *,
    result: dict[str, Any],
    image: ValidatedImage,
    current_user: User | None,
    requested_farm_id: int | None,
) -> dict[str, Any]:
    """Ghép metadata và persist đúng một Scan/TopK cho user đăng nhập."""
    # Status is authoritative; never let a stale legacy flag expose treatment.
    result = dict(result)
    result["is_valid_leaf"] = result["validation_status"] == "accepted"
    if not result["is_valid_leaf"]:
        result["label"] = None
    disease_payload = _disease_payload(db, result)
    base_response = {
        "label": result["label"],
        "confidence": result["confidence"],
        "is_valid_leaf": result["is_valid_leaf"],
        "top_k": result["top_k"],
        "model_version": result["model_version"],
        "inference_mode": result["inference_mode"],
        "inference_strategy": result.get("inference_strategy", "ensemble"),
        "selected_model_type": result.get("selected_model_type"),
        "decision_details": result.get("decision_details", {}),
        "validation_status": result["validation_status"],
        "rejection_reason": result["rejection_reason"],
        "agreement_status": result["agreement_status"],
        "agreement_count": result["agreement_count"],
        "models_requested": result["models_requested"],
        "models_succeeded": result["models_succeeded"],
        "top1_top2_margin": result["top1_top2_margin"],
        "ensemble_entropy": result["ensemble_entropy"],
        "js_divergence": result["js_divergence"],
        "energy_score": result["energy_score"],
        "ood_score": result["ood_score"],
        "policy_version": result["policy_version"],
        "model_results": result["model_results"],
        **disease_payload,
    }

    if current_user is None:
        return PredictResponse.model_validate({
            **base_response,
            "scan_id": None,
            "farm_id": None,
            "farm_assignment_status": "not_applicable",
        }).model_dump()

    # Account state may change while inference runs. This is persistence/RBAC,
    # not a change to model execution or prediction thresholds.
    expected_version = current_user.token_version
    user = db.query(User).filter(User.id == current_user.id).populate_existing().with_for_update().first()
    if user is None or user.status != "active" or user.token_version != expected_version:
        db.rollback()
        raise HTTPException(status_code=401, detail="Phiên đăng nhập không còn hiệu lực; không lưu Scan")
    current_user = user
    assigned_farm_id, farm_status, farm_warning = _resolve_farm(
        db,
        current_user,
        requested_farm_id,
    )
    if farm_warning:
        existing_warning = base_response.get("warning")
        base_response["warning"] = (
            f"{existing_warning} {farm_warning}"
            if existing_warning
            else farm_warning
        )

    image_path: str | None = None
    try:
        PredictResponse.model_validate({**base_response, "farm_id": assigned_farm_id,
                                       "farm_assignment_status": farm_status})
        image_path = save_image(image)
        scan = Scan(
            user_id=current_user.id,
            farm_id=assigned_farm_id,
            image_path=image_path,
            predicted_label=result["label"],
            confidence=result["confidence"],
            is_valid_leaf=result["is_valid_leaf"],
            model_version=result["model_version"],
            primary_model_version_id=result["primary_model_version_id"],
            inference_mode=result["inference_mode"],
            validation_status=result["validation_status"],
            rejection_reason=result["rejection_reason"],
            agreement_status=result["agreement_status"],
            top1_top2_margin=result["top1_top2_margin"],
            ensemble_entropy=result["ensemble_entropy"],
            js_divergence=result["js_divergence"],
            energy_score=result["energy_score"],
            ood_score=result["ood_score"],
            policy_version=result["policy_version"],
            prediction_context={"schema_version": 1,
                                "inference_strategy": base_response["inference_strategy"],
                                "selected_model_type": base_response["selected_model_type"],
                                "decision_details": base_response["decision_details"]},
        )
        db.add(scan)
        db.flush()
        db.add_all(
            [
                ScanTopK(
                    scan_id=scan.id,
                    label=item["label"],
                    confidence=item["confidence"],
                    rank=item["rank"],
                )
                for item in result["top_k"]
            ]
        )
        db.add_all(
            [
                ScanModelResult(
                    scan_id=scan.id,
                    model_version_id=item["model_version_id"],
                    execution_order=item["execution_order"],
                    predicted_label=item["predicted_label"],
                    confidence=item["confidence"],
                    top1_top2_margin=item["top1_top2_margin"],
                    entropy=item["entropy"],
                    energy_score=item["energy_score"],
                    accepted=item["accepted"],
                    latency_ms=item["latency_ms"],
                    error_code=item["error_code"],
                    topk_json=json.dumps(item["top_k"], ensure_ascii=False),
                )
                for item in result["model_results"]
            ]
        )
        scan_id = scan.id
        db.commit()
    except (OSError, SQLAlchemyError, KeyError, TypeError, ValueError) as exc:
        db.rollback()
        if image_path is not None:
            try:
                delete_stored_image(image_path)
            except OSError:
                logger.exception("Không thể dọn file sau khi persist predict thất bại")
        logger.exception("Không thể persist kết quả predict")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể lưu kết quả dự đoán.",
        ) from exc

    return {
        **base_response,
        "scan_id": scan_id,
        "farm_id": assigned_farm_id,
        "farm_assignment_status": farm_status,
    }
