"""Business rules khi Manager phân công Managed User vào Farm."""

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crud import farm as farm_crud
from app.crud import farm_member as member_crud
from app.crud import user as user_crud
from app.models.farm import Farm
from app.models.farm_member import FarmMember
from app.models.user import User


def _get_owned_farm(db: Session, manager: User, farm_id: int) -> Farm:
    farm = farm_crud.get_farm_by_id(db, farm_id)
    if farm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy farm",
        )
    if farm.owner_id != manager.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không sở hữu farm này",
        )
    return farm


def add_member(
    db: Session,
    *,
    manager: User,
    farm_id: int,
    user_id: int,
) -> FarmMember:
    """Gán một Managed User của Manager vào Farm do họ sở hữu."""
    _get_owned_farm(db, manager, farm_id)
    user = user_crud.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy user",
        )
    if user.role != "user" or user.created_by != manager.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ được gán User do chính Manager này tạo",
        )
    if member_crud.get_membership(
        db,
        farm_id=farm_id,
        user_id=user_id,
    ) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User đã là thành viên của farm",
        )

    membership = FarmMember(
        farm_id=farm_id,
        user_id=user_id,
        added_by=manager.id,
    )
    db.add(membership)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User đã là thành viên của farm",
        ) from exc
    db.refresh(membership)
    return member_crud.get_membership(
        db,
        farm_id=farm_id,
        user_id=user_id,
    ) or membership


def list_members(
    db: Session,
    *,
    manager: User,
    farm_id: int,
) -> list[FarmMember]:
    """Liệt kê thành viên nếu Manager sở hữu Farm."""
    _get_owned_farm(db, manager, farm_id)
    return member_crud.get_members_by_farm(db, farm_id)


def remove_member(
    db: Session,
    *,
    manager: User,
    farm_id: int,
    user_id: int,
) -> None:
    """Gỡ User khỏi Farm nhưng không xóa tài khoản User."""
    _get_owned_farm(db, manager, farm_id)
    membership = member_crud.get_membership(
        db,
        farm_id=farm_id,
        user_id=user_id,
    )
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User không phải thành viên của farm",
        )
    db.delete(membership)
    db.commit()
