"""API endpoint tra cứu và quản lý thông tin bệnh."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.disease_info import (
    DiseaseInfoCreate, DiseaseInfoUpdate, DiseaseInfoResponse
)
from app.services import disease_info_service
from app.api.deps import require_role
from app.models.user import User

router = APIRouter(prefix="/disease-info", tags=["Disease Info"])


@router.get("", response_model=list[DiseaseInfoResponse])
def list_diseases(db: Session = Depends(get_db)):
    """Danh sách toàn bộ bệnh — Public, không cần đăng nhập."""
    return disease_info_service.list_diseases(db)


@router.get("/{label_key}", response_model=DiseaseInfoResponse)
def get_disease(label_key: str, db: Session = Depends(get_db)):
    """Chi tiết 1 bệnh — Public."""
    return disease_info_service.get_disease(db, label_key)


@router.post("",
             response_model=DiseaseInfoResponse,
             status_code=status.HTTP_201_CREATED)
def create_disease(
    data: DiseaseInfoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Thêm bệnh mới — chỉ Admin."""
    return disease_info_service.create_disease(db, current_user.id, data)


@router.put("/{label_key}", response_model=DiseaseInfoResponse)
def update_disease(
    label_key: str,
    data: DiseaseInfoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Cập nhật bệnh — chỉ Admin."""
    return disease_info_service.update_disease(
        db, current_user.id, label_key, data
    )


@router.delete("/{label_key}")
def delete_disease(
    label_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Xóa bệnh — chỉ Admin."""
    disease_info_service.delete_disease(db, label_key)
    return {"message": "Đã xóa bệnh thành công"}
