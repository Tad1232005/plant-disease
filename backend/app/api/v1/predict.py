"""API endpoint dự đoán bệnh lá cây từ ảnh."""

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.predict import PredictResponse
from app.services.predict_service import predict_service

router = APIRouter(prefix="/predict", tags=["Predict"])


@router.post("", response_model=PredictResponse)
async def predict_disease(file: UploadFile = File(...)):
    """Nhận ảnh lá cây, trả về nhãn bệnh + độ tin cậy."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400, detail="File phải là ảnh (jpg/png)."
        )

    image_bytes = await file.read()
    result = predict_service.predict(image_bytes)
    return PredictResponse(**result)