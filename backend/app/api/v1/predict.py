"""API endpoint dự đoán bệnh lá cây từ ảnh."""

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from app.schemas.predict import PredictResponse
from app.services.predict_service import predict_service

router = APIRouter(prefix="/predict", tags=["AI Prediction"])


@router.post("", response_model=PredictResponse)
async def predict_plant_disease(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File tải lên phải là định dạng hình ảnh (JPEG/PNG).",
        )

    try:
        contents = await file.read()
        # Nếu predict_service.predict là sync:
        from fastapi.concurrency import run_in_threadpool
        return await run_in_threadpool(predict_service.predict, contents)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi xử lý AI: {str(e)}",
        )
