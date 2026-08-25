"""Schema cho DiseaseInfo (nội dung tra cứu bệnh)."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

SeverityLevel = Literal["low", "medium", "high"]


class DiseaseInfoCreate(BaseModel):
    """Dữ liệu đầu vào khi Admin thêm bệnh mới."""

    label_key: str = Field(min_length=1, max_length=50)
    disease_name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    treatment: Optional[str] = None
    severity_level: SeverityLevel = "medium"

    @field_validator("label_key", "disease_name")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Giá trị không được để trống")
        return value


class DiseaseInfoUpdate(BaseModel):
    """Dữ liệu đầu vào khi Admin sửa nội dung bệnh."""

    disease_name: Optional[str] = Field(
        default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    treatment: Optional[str] = None
    severity_level: Optional[SeverityLevel] = None

    @field_validator("disease_name")
    @classmethod
    def strip_disease_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Tên bệnh không được để trống")
        return value


class DiseaseInfoResponse(BaseModel):
    """Dữ liệu trả về khi tra cứu thông tin bệnh."""

    id: int
    label_key: str
    disease_name: str
    description: Optional[str] = None
    treatment: Optional[str] = None
    severity_level: SeverityLevel
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
