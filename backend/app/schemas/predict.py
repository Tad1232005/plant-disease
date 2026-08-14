"""Schema cho request/response của API predict."""

from typing import Dict

from pydantic import BaseModel


class PredictResponse(BaseModel):
    """Kết quả trả về sau khi model dự đoán 1 ảnh."""

    label: str
    confidence: float
    is_valid_leaf: bool
    all_probs: Dict[str, float]