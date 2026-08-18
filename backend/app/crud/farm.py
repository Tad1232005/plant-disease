"""Thao tác CSDL cho bảng farms."""

from sqlalchemy.orm import Session
from app.models.farm import Farm
from app.schemas.farm import FarmCreate, FarmUpdate


def create_farm(db: Session, user_id: int, farm_in: FarmCreate) -> Farm:
    """Tạo mới 1 farm thuộc về user_id."""
    db_farm = Farm(
        user_id=user_id, name=farm_in.name, location_text=farm_in.location_text
    )
    db.add(db_farm)
    db.commit()
    db.refresh(db_farm)
    return db_farm


def get_farms_by_user(db: Session, user_id: int) -> list[Farm]:
    """Lấy toàn bộ farm thuộc về 1 user."""
    return db.query(Farm).filter(Farm.user_id == user_id).all()


def get_farm_by_id(db: Session, farm_id: int) -> Farm | None:
    """Lấy 1 farm theo id."""
    return db.query(Farm).filter(Farm.id == farm_id).first()


def update_farm(db: Session, db_farm: Farm, farm_in: FarmUpdate) -> Farm:
    """Cập nhật thông tin farm."""
    if farm_in.name is not None:
        db_farm.name = farm_in.name
    if farm_in.location_text is not None:
        db_farm.location_text = farm_in.location_text
    db.commit()
    db.refresh(db_farm)
    return db_farm


def delete_farm(db: Session, db_farm: Farm) -> None:
    """Xóa 1 farm."""
    db.delete(db_farm)
    db.commit()
