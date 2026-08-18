"""Schema cho DiseaseInfo (nội dung tra cứu bệnh)."""

from typing import Optional
from pydantic import BaseModel


class DiseaseInfoCreate(BaseModel):
    """Dữ liệu đầu vào khi Admin thêm bệnh mới."""

    label_key: str
    disease_name: str
    description: Optional[str] = None
    treatment: Optional[str] = None
    severity_level: str = "medium"


class DiseaseInfoUpdate(BaseModel):
    """Dữ liệu đầu vào khi Admin sửa nội dung bệnh."""

    disease_name: Optional[str] = None
    description: Optional[str] = None
    treatment: Optional[str] = None
    severity_level: Optional[str] = None


class DiseaseInfoResponse(BaseModel):
    """Dữ liệu trả về khi tra cứu thông tin bệnh."""

    id: int
    label_key: str
    disease_name: str
    description: Optional[str] = None
    treatment: Optional[str] = None
    severity_level: str

    class Config:
        """Cho phép đọc trực tiếp từ SQLAlchemy object."""

        from_attributes = True
