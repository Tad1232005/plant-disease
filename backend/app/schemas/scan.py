"""Schema cho Scan (lịch sử chẩn đoán)."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class ScanHistoryItem(BaseModel):
    """1 dòng trong danh sách lịch sử scan."""

    id: int
    predicted_label: Optional[str] = None
    confidence: Optional[float] = None
    is_valid_leaf: bool
    created_at: datetime

    class Config:
        """Cho phép đọc trực tiếp từ SQLAlchemy object."""

        from_attributes = True


class ScanTopKItem(BaseModel):
    """1 dòng xác suất trong top-3."""

    label: str
    confidence: float
    rank: int

    class Config:
        """Cho phép đọc trực tiếp từ SQLAlchemy object."""

        from_attributes = True


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
    top3: List[ScanTopKItem] = []

    class Config:
        """Cho phép đọc trực tiếp từ SQLAlchemy object."""

        from_attributes = True
