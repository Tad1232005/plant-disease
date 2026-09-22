"""Schemas cho Model Version API — chỉ Admin mới thao tác."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ModelVersionBase(BaseModel):
    version_name: str
    model_type: str
    task: str
    temperature: float
    is_active: bool
    is_enabled: bool
    accuracy: Optional[float] = None
    macro_f1: Optional[float] = None
    ece: Optional[float] = None


class ModelVersionResponse(ModelVersionBase):
    """Chi tiết một Model Version trả về cho Admin."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    file_path: str
    classes_path: Optional[str] = None
    temperature_path: Optional[str] = None
    sha256: Optional[str] = None
    metrics_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ModelVersionListItem(BaseModel):
    """Dòng rút gọn trong danh sách Model Version."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    version_name: str
    model_type: str
    is_active: bool
    is_enabled: bool
    temperature: float
    accuracy: Optional[float] = None
    macro_f1: Optional[float] = None
    created_at: datetime


class RegisterModelVersionRequest(BaseModel):
    """Đường dẫn tới manifest.json trên server để đăng ký version mới."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    manifest_path: str = Field(
        min_length=1,
        max_length=500,
        description="Đường dẫn tuyệt đối tới file manifest.json của bundle ML.",
    )
    accuracy: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    macro_f1: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    ece: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    metrics_path: Optional[str] = Field(default=None, max_length=500)


class ActivateModelVersionResponse(ModelVersionResponse):
    """Response khi activate version — kèm thông tin version bị deactivate."""

    deactivated_version_id: Optional[int] = None
    deactivated_version_name: Optional[str] = None
    warmup_latency_ms: Optional[float] = None
