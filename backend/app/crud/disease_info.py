"""Thao tác CSDL cho bảng disease_info."""

from sqlalchemy.orm import Session
from app.models.disease_info import DiseaseInfo
from app.schemas.disease_info import DiseaseInfoCreate, DiseaseInfoUpdate


def get_all_disease_info(
    db: Session,
    *,
    include_inactive: bool = False,
) -> list[DiseaseInfo]:
    """Lấy danh sách bệnh; mặc định chỉ lấy nội dung đang công khai."""
    query = db.query(DiseaseInfo)
    if not include_inactive:
        query = query.filter(DiseaseInfo.is_active.is_(True))
    return query.order_by(DiseaseInfo.label_key).all()


def get_disease_info_by_label(
    db: Session,
    label_key: str,
    *,
    include_inactive: bool = False,
) -> DiseaseInfo | None:

    """Lấy 1 bệnh theo label_key."""
    query = db.query(DiseaseInfo).filter(DiseaseInfo.label_key == label_key)
    if not include_inactive:
        query = query.filter(DiseaseInfo.is_active.is_(True))
    return query.first()


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
    """Ẩn nội dung bệnh khỏi API public nhưng giữ cho scan lịch sử."""
    db_item.is_active = False
    db.add(db_item)
    db.commit()
