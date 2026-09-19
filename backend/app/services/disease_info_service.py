"""Business logic cho DiseaseInfo."""

from sqlalchemy.orm import Session
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from app.crud import disease_info as disease_crud
from app.schemas.disease_info import DiseaseInfoCreate, DiseaseInfoUpdate


def list_diseases(db: Session, *, limit: int = 50, offset: int = 0):
    """Lấy toàn bộ danh sách bệnh (public)."""
    return disease_crud.get_all_disease_info(db, limit=limit, offset=offset)


def get_disease(db: Session, label_key: str):
    """Lấy chi tiết 1 bệnh theo label_key."""
    item = disease_crud.get_disease_info_by_label(db, label_key)
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy bệnh này")
    return item


def create_disease(db: Session, admin_id: int, data: DiseaseInfoCreate):
    """Admin thêm bệnh mới hoặc khôi phục label đã soft-delete."""
    existing = disease_crud.lock_disease(db, data.label_key)
    if existing and existing.is_active:
        raise HTTPException(status_code=400, detail="label_key đã tồn tại")
    if existing:
        for field, value in data.model_dump().items():
            setattr(existing, field, value)
        existing.is_active = True
        existing.content_version += 1
        existing.updated_by = admin_id
        db.commit()
        db.refresh(existing)
        return existing
    try:
        return disease_crud.create_disease_info(db, admin_id, data)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Nhãn vừa được tạo; hãy tải lại danh mục") from exc


def update_disease(
        db: Session, admin_id: int, label_key: str, data: DiseaseInfoUpdate):
    """Admin cập nhật bệnh."""
    item = disease_crud.lock_disease(db, label_key)
    if item is None or not item.is_active:
        raise HTTPException(status_code=404, detail="Không tìm thấy bệnh này")
    return disease_crud.update_disease_info(db, item, admin_id, data)


def delete_disease(db: Session, label_key: str):
    """Admin ẩn bệnh khỏi danh mục public (soft delete)."""
    item = disease_crud.lock_disease(db, label_key)
    if item is None or not item.is_active:
        raise HTTPException(status_code=404, detail="Không tìm thấy bệnh này")
    disease_crud.delete_disease_info(db, item)
