"""API inference public, có persistence khi request đã đăng nhập."""

import asyncio
import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_optional
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.predict import (
    PredictCapabilitiesResponse,
    PredictResponse,
    RequestedMode,
    InferenceStrategy,
    ModelType,
)
from app.services.image_storage_service import UploadValidationError, validate_upload
from app.services.prediction_workflow_service import complete_prediction
from app.services.predict_service import (
    InferenceCapacityError,
    ModelConfigurationError,
    ModeNotAllowedError,
    capabilities_for_role,
    get_active_models,
    predict_service,
    resolve_mode,
)

router = APIRouter(prefix="/predict", tags=["AI Prediction"])
logger = logging.getLogger(__name__)


@router.get("/capabilities", response_model=PredictCapabilitiesResponse)
def get_predict_capabilities(
    current_user: User | None = Depends(get_current_user_optional),
) -> dict:
    """Cho FE biết mode nào được dùng; quyền thật vẫn do server kiểm tra."""
    return capabilities_for_role(current_user.role if current_user else None)


@router.post("", response_model=PredictResponse)
async def predict_plant_disease(
    file: UploadFile = File(...),
    farm_id: int | None = Form(default=None, ge=1),
    mode: RequestedMode = Form(default="auto"),
    strategy: InferenceStrategy = Form(default="ensemble"),
    model_type: ModelType | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> dict:
    """Predict cho Guest; lưu Scan/TopK và kiểm tra Farm nếu đã đăng nhập."""
    if (strategy == "single") != (model_type is not None):
        await file.close()
        raise HTTPException(status_code=422, detail="single cần model_type; ensemble không nhận model_type.")
    if current_user is None and farm_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Guest không được gửi farm_id.",
        )

    try:
        image = await validate_upload(file)
    except UploadValidationError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.detail,
        ) from exc
    finally:
        await file.close()

    try:
        resolved_mode = resolve_mode(
            current_user.role if current_user else None,
            mode,
        )
        active_models = get_active_models(db, resolved_mode, model_type=model_type)
    except ModeNotAllowedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except ModelConfigurationError as exc:
        logger.error("Cấu hình model chưa sẵn sàng: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Các model cần thiết cho chế độ này chưa sẵn sàng.",
        ) from exc

    try:
        result = await asyncio.wait_for(
            run_in_threadpool(
                predict_service.predict_bounded,
                image.data,
                active_models,
                resolved_mode,
            ),
            timeout=settings.INFERENCE_TIMEOUT_SECONDS,
        )
    except TimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Mô hình xử lý quá thời gian cho phép.",
        ) from exc
    except InferenceCapacityError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Hệ thống đang bận xử lý chẩn đoán, vui lòng thử lại.",
        ) from exc
    except Exception as exc:
        logger.exception("Inference thất bại")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Mô hình tạm thời không thể xử lý ảnh.",
        ) from exc

    result["inference_strategy"] = strategy
    result["selected_model_type"] = model_type
    return await run_in_threadpool(
        complete_prediction,
        db,
        result=result,
        image=image,
        current_user=current_user,
        requested_farm_id=farm_id,
    )
