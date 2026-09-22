"""API Admin quản lý tài khoản Technician/Manager."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (
    AdminCreateUserRequest,
    UserResponse,
    UserRole,
    UserStatusRequest,
)
from app.services import user_admin_service

router = APIRouter(prefix="/admin/users", tags=["Admin Users"])


@router.patch("/{user_id}/status", response_model=UserResponse)
def change_user_status(
    user_id: int,
    data: UserStatusRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_role("admin")),
) -> User:
    """Admin suspend hoặc activate tài khoản bất kỳ."""
    return user_admin_service.set_user_status(db, actor=actor, user_id=user_id, data=data)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_admin_managed_user(
    data: AdminCreateUserRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_role("admin")),
) -> User:
    """Admin tạo Technician hoặc Manager."""
    return user_admin_service.create_user_by(
        db,
        creator=current_admin,
        data=data,
        role=data.role,
    )


@router.get("", response_model=list[UserResponse])
def list_users(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    role: UserRole | None = Query(default=None),
    db: Session = Depends(get_db),
    _current_admin: User = Depends(require_role("admin")),
) -> list[User]:
    """Admin xem user toàn hệ thống, tùy chọn lọc theo role."""
    return user_admin_service.list_users_for_admin(db, role=role, limit=limit, offset=offset)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _current_admin: User = Depends(require_role("admin")),
) -> User:
    """Admin xem chi tiết bất kỳ tài khoản nào trong hệ thống."""
    return user_admin_service.get_user_for_admin(db, user_id)
