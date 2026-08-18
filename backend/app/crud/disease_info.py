"""Thao tác CSDL cho bảng disease_info."""

from sqlalchemy.orm import Session
from app.models.disease_info import DiseaseInfo
from app.schemas.disease_info import DiseaseInfoCreate, DiseaseInfoUpdate


def get_all_disease_info(db: Session) -> list[DiseaseInfo]:
    """Lấy toàn bộ danh sách bệnh."""
    return db.query(DiseaseInfo).all()


def get_disease_info_by_label(
        db: Session, label_key: str) -> DiseaseInfo | None:

    """Lấy 1 bệnh theo label_key."""
    return db.query(DiseaseInfo).filter(
        DiseaseInfo.label_key == label_key
    ).first()


def create_disease_info(
        db: Session, admin_id: int, data: DiseaseInfoCreate) -> DiseaseInfo:

    """Admin thêm 1 bệnh mới."""
    db_item = DiseaseInfo(**data.model_dump(), updated_by=admin_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def update_disease_info(
    db: Session, db_item: DiseaseInfo, admin_id: int, data: DiseaseInfoUpdate
) -> DiseaseInfo:
    """Admin cập nhật nội dung bệnh."""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(db_item, field, value)
    db_item.updated_by = admin_id
    db.commit()
    db.refresh(db_item)
    return db_item


def delete_disease_info(db: Session, db_item: DiseaseInfo) -> None:
    """Admin xóa 1 bệnh."""
    db.delete(db_item)
    db.commit()
