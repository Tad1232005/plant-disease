"""Thao tác CSDL cho bảng farms."""

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


def get_farms_by_user(db: Session, user_id: int) -> list[Farm]:
    """Lấy toàn bộ farm thuộc về 1 user."""
    return (
        db.query(Farm)
        .filter(Farm.owner_id == user_id)
        .order_by(Farm.created_at.desc(), Farm.id.desc())
        .all()
    )


def get_all_farms(db: Session) -> list[Farm]:
    """Lấy toàn bộ farm; chỉ service dành cho Admin được gọi hàm này."""
    return db.query(Farm).order_by(Farm.created_at.desc(), Farm.id.desc()).all()


def get_farm_by_id(db: Session, farm_id: int) -> Farm | None:
    """Lấy 1 farm theo id."""
    return db.query(Farm).filter(Farm.id == farm_id).first()


def update_farm(db: Session, db_farm: Farm, farm_in: FarmUpdate) -> Farm:
    """Cập nhật thông tin farm."""
    for field, value in farm_in.model_dump(exclude_unset=True).items():
        setattr(db_farm, field, value)
    db.commit()
    db.refresh(db_farm)
    return db_farm


def delete_farm(db: Session, db_farm: Farm) -> None:
    """Xóa 1 farm."""
    db.delete(db_farm)
    db.commit()
