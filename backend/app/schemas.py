from pydantic import BaseModel


class PredictResponse(BaseModel):
    label: str          # tên bệnh dự đoán, vd: "Tomato___Early_blight"
    confidence: float   # độ tin cậy, vd: 0.9421 (=94.21%)
