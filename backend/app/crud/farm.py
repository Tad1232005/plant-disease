"""Thao tác CSDL cho bảng farms."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session
from app.models.farm import Farm
from app.schemas.farm import FarmCreate, FarmUpdate


def create_farm(db: Session, user_id: int, farm_in: FarmCreate) -> Farm:
    """Tạo mới 1 farm thuộc về user_id."""
    db_farm = Farm(
        owner_id=user_id, name=farm_in.name, location_text=farm_in.location_text
    )
    db.add(db_farm)
    db.commit()
    db.refresh(db_farm)
    return db_farm


def get_farms_by_user(db: Session, user_id: int, *, limit: int = 50, offset: int = 0) -> list[Farm]:
    """Lấy toàn bộ farm thuộc về 1 user."""
    return (
        db.query(Farm)
        .filter(Farm.owner_id == user_id, Farm.archived_at.is_(None))
        .order_by(Farm.created_at.desc(), Farm.id.desc())
        .offset(offset).limit(limit)
        .all()
    )


def get_farm_by_id(db: Session, farm_id: int, *, for_update: bool = False) -> Farm | None:
    """Lấy 1 farm theo id."""
    query = (
        db.query(Farm)
        .filter(Farm.id == farm_id, Farm.archived_at.is_(None))
    )
    if for_update:
        query = query.populate_existing().with_for_update()
    return query.first()


def update_farm(db: Session, db_farm: Farm, farm_in: FarmUpdate) -> Farm:
    """Cập nhật thông tin farm."""
    for field, value in farm_in.model_dump(exclude_unset=True).items():
        setattr(db_farm, field, value)
    db.commit()
    db.refresh(db_farm)
    return db_farm


def delete_farm(db: Session, db_farm: Farm) -> None:
    """Ẩn farm khỏi nghiệp vụ nhưng giữ nguyên dữ liệu scan lịch sử."""
    db_farm.archived_at = datetime.now(timezone.utc)
    db.add(db_farm)
    db.commit()
