"""Schema cho Farm (khu vực/trang trại)."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FarmCreate(BaseModel):
    """Dữ liệu đầu vào khi tạo farm mới."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=100)
    location_text: Optional[str] = Field(default=None, max_length=255)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Tên farm không được để trống")
        return value


class FarmUpdate(BaseModel):
    """Dữ liệu đầu vào khi cập nhật farm."""

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    location_text: Optional[str] = Field(default=None, max_length=255)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            raise ValueError("Tên farm không được là null")
        value = value.strip()
        if not value:
            raise ValueError("Tên farm không được để trống")
        return value


class FarmResponse(BaseModel):
    """Dữ liệu trả về khi lấy thông tin farm."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    location_text: Optional[str] = None
    owner_id: int
    created_at: datetime
