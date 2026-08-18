"""Schema cho Farm (khu vực/trang trại)."""

from typing import Optional
from pydantic import BaseModel


class FarmCreate(BaseModel):
    """Dữ liệu đầu vào khi tạo farm mới."""

    name: str
    location_text: Optional[str] = None


class FarmUpdate(BaseModel):
    """Dữ liệu đầu vào khi cập nhật farm."""

    name: Optional[str] = None
    location_text: Optional[str] = None


class FarmResponse(BaseModel):
    """Dữ liệu trả về khi lấy thông tin farm."""

    id: int
    name: str
    location_text: Optional[str] = None

    class Config:
        """Cho phép đọc trực tiếp từ SQLAlchemy object."""

        from_attributes = True
