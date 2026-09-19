"""Business logic cho Farm."""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.crud import farm as farm_crud
from app.schemas.farm import FarmCreate, FarmUpdate
from app.models.user import User
from app.services.account_control_service import lock_active_actor


def _check_owner(farm, current_user: User) -> None:
    """Chỉ Manager sở hữu farm mới được thao tác trên farm này."""
    if farm.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Không có quyền"
            )


def create_farm(db: Session, current_user: User, farm_in: FarmCreate):
    """Tạo farm mới cho user hiện tại."""
    current_user = lock_active_actor(db, current_user, {"manager"})
    return farm_crud.create_farm(db, current_user.id, farm_in)


def list_farms(db: Session, current_user: User, *, limit: int = 50, offset: int = 0):
    """Lấy danh sách farm của user hiện tại."""
    return farm_crud.get_farms_by_user(db, current_user.id, limit=limit, offset=offset)


def get_farm(db: Session, current_user: User, farm_id: int):
    """Lấy chi tiết farm sau khi kiểm tra phạm vi sở hữu."""
    db_farm = farm_crud.get_farm_by_id(db, farm_id)
    if not db_farm:
        raise HTTPException(status_code=404, detail="Không tìm thấy farm")
    _check_owner(db_farm, current_user)
    return db_farm


def update_farm(
        db: Session, current_user: User, farm_id: int, farm_in: FarmUpdate):
    """Cập nhật farm, kiểm tra quyền sở hữu."""
    db_farm = get_farm(db, current_user, farm_id)
    return farm_crud.update_farm(db, db_farm, farm_in)


def delete_farm(db: Session, current_user: User, farm_id: int):
    """Lưu trữ farm (soft delete), sau khi kiểm tra quyền sở hữu."""
    db_farm = get_farm(db, current_user, farm_id)
    farm_crud.delete_farm(db, db_farm)
