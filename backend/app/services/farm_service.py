"""Business logic cho Farm."""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.crud import farm as farm_crud
from app.schemas.farm import FarmCreate, FarmUpdate
from app.models.user import User


def _check_owner_or_admin(farm, current_user: User) -> None:
    """Chỉ chủ sở hữu hoặc admin mới được thao tác trên farm này."""
    if farm.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Không có quyền"
            )


def create_farm(db: Session, current_user: User, farm_in: FarmCreate):
    """Tạo farm mới cho user hiện tại."""
    return farm_crud.create_farm(db, current_user.id, farm_in)


def list_farms(db: Session, current_user: User):
    """Lấy danh sách farm của user hiện tại."""
    return farm_crud.get_farms_by_user(db, current_user.id)


def update_farm(
        db: Session, current_user: User, farm_id: int, farm_in: FarmUpdate):
    """Cập nhật farm, kiểm tra quyền sở hữu."""
    db_farm = farm_crud.get_farm_by_id(db, farm_id)
    if not db_farm:
        raise HTTPException(status_code=404, detail="Không tìm thấy farm")
    _check_owner_or_admin(db_farm, current_user)
    return farm_crud.update_farm(db, db_farm, farm_in)


def delete_farm(db: Session, current_user: User, farm_id: int):
    """Xóa farm, kiểm tra quyền sở hữu."""
    db_farm = farm_crud.get_farm_by_id(db, farm_id)
    if not db_farm:
        raise HTTPException(status_code=404, detail="Không tìm thấy farm")
    _check_owner_or_admin(db_farm, current_user)
    farm_crud.delete_farm(db, db_farm)
