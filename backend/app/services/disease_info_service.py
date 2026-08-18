"""Business logic cho DiseaseInfo."""

from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.crud import disease_info as disease_crud
from app.schemas.disease_info import DiseaseInfoCreate, DiseaseInfoUpdate


def list_diseases(db: Session):
    """Lấy toàn bộ danh sách bệnh (public)."""
    return disease_crud.get_all_disease_info(db)


def get_disease(db: Session, label_key: str):
    """Lấy chi tiết 1 bệnh theo label_key."""
    item = disease_crud.get_disease_info_by_label(db, label_key)
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy bệnh này")
    return item


def create_disease(db: Session, admin_id: int, data: DiseaseInfoCreate):
    """Admin thêm bệnh mới, chặn trùng label_key."""
    if disease_crud.get_disease_info_by_label(db, data.label_key):
        raise HTTPException(status_code=400, detail="label_key đã tồn tại")
    return disease_crud.create_disease_info(db, admin_id, data)


def update_disease(
        db: Session, admin_id: int, label_key: str, data: DiseaseInfoUpdate):
    """Admin cập nhật bệnh."""
    item = get_disease(db, label_key)
    return disease_crud.update_disease_info(db, item, admin_id, data)


def delete_disease(db: Session, label_key: str):
    """Admin xóa bệnh."""
    item = get_disease(db, label_key)
    disease_crud.delete_disease_info(db, item)
