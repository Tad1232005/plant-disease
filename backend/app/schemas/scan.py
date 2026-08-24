"""Schema cho Scan (lịch sử chẩn đoán)."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ScanHistoryItem(BaseModel):
    """1 dòng trong danh sách lịch sử scan."""

    id: int
    predicted_label: Optional[str] = None
    confidence: Optional[float] = None
    is_valid_leaf: bool
    created_at: datetime

class ScanTopKItem(BaseModel):
    """1 dòng xác suất trong top-3."""

    label: str
    confidence: float
    rank: int

class ScanDetailResponse(BaseModel):
    """Chi tiết đầy đủ 1 lượt scan, kèm tên bệnh và gợi ý xử lý."""

    id: int
    predicted_label: Optional[str] = None
    confidence: Optional[float] = None
    is_valid_leaf: bool
    gradcam_path: Optional[str] = None
    created_at: datetime
    disease_name: Optional[str] = None
    treatment: Optional[str] = None
    top3: list[ScanTopKItem] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)

    model_config = ConfigDict(from_attributes=True)

    model_config = ConfigDict(from_attributes=True)
