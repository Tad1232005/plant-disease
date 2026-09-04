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
)
from app.services import user_admin_service

router = APIRouter(prefix="/admin/users", tags=["Admin Users"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
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
    role: UserRole | None = Query(default=None),
    db: Session = Depends(get_db),
    _current_admin: User = Depends(require_role("admin")),
) -> list[User]:
    """Admin xem user toàn hệ thống, tùy chọn lọc theo role."""
    return user_admin_service.list_users_for_admin(db, role=role)
