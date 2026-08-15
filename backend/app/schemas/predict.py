"""Schema cho request/response của API predict."""

from typing import List

from pydantic import BaseModel, Field


class TopKResult(BaseModel):
    label: str = Field(..., description="Tên nhãn bệnh")
    confidence: float = Field(..., description="Độ tin cậy (0.0 đến 1.0)")
    rank: int = Field(..., description="Thứ tự xếp hạng (1, 2, 3)")


class PredictResponse(BaseModel):
    label: str = Field(..., description="Tên bệnh có độ tin cậy cao nhất")
    confidence: float = Field(..., description="Độ tin cậy của nhãn cao nhất")
    top_k: List[TopKResult] = Field(
        ..., description="Top 3 kết quả khả thi nhất"
    )