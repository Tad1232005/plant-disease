"""Thao tác CSDL cho bảng disease_info."""

from sqlalchemy.orm import Session
from app.models.disease_info import DiseaseInfo
from app.schemas.disease_info import DiseaseInfoCreate, DiseaseInfoUpdate


def get_all_disease_info(
    db: Session,
    *,
    include_inactive: bool = False,
    limit: int | None = None,
    offset: int = 0,
) -> list[DiseaseInfo]:
    """Lấy danh sách bệnh; mặc định chỉ lấy nội dung đang công khai."""
    query = db.query(DiseaseInfo)
    if not include_inactive:
        query = query.filter(DiseaseInfo.is_active.is_(True))
    query = query.order_by(DiseaseInfo.label_key).offset(offset)
    if limit is not None:
        query = query.limit(limit)
    return query.all()


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


def lock_disease(db: Session, label_key: str) -> DiseaseInfo | None:
    return db.query(DiseaseInfo).filter(DiseaseInfo.label_key == label_key).populate_existing().with_for_update().first()


def apply_content(db_item: DiseaseInfo, admin_id: int, data: DiseaseInfoUpdate) -> None:
    """Shared mutation for direct CRUD and approval; caller owns transaction."""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(db_item, field, value)
    db_item.updated_by = admin_id
    db_item.content_version += 1


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
    apply_content(db_item, admin_id, data)
    db.commit()
    db.refresh(db_item)
    return db_item


def delete_disease_info(db: Session, db_item: DiseaseInfo) -> None:
    """Ẩn nội dung bệnh khỏi API public nhưng giữ cho scan lịch sử."""
    db_item.is_active = False
    db_item.content_version += 1
    db.add(db_item)
    db.commit()
