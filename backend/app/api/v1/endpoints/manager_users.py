"""API Manager quản lý Managed User của chính mình."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (
    ManagerCreateUserRequest,
    ManagerResetPasswordRequest,
    UserResponse,
    UserStatusRequest,
)
from app.services import user_admin_service

router = APIRouter(prefix="/manager/users", tags=["Manager Users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_managed_user(
    data: ManagerCreateUserRequest,
    db: Session = Depends(get_db),
    current_manager: User = Depends(require_role("manager")),
) -> User:
    """Manager tạo User; role luôn được hardcode tại service."""
    return user_admin_service.create_user_by(
        db,
        creator=current_manager,
        data=data,
        role="user",
    )


@router.get("", response_model=list[UserResponse])
def list_managed_users(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_manager: User = Depends(require_role("manager")),
) -> list[User]:
    """Manager chỉ xem User do chính mình tạo."""
    return user_admin_service.list_managed_users(
        db,
        manager_id=current_manager.id,
        limit=limit,
        offset=offset,
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_managed_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_manager: User = Depends(require_role("manager")),
) -> User:
    """Manager xem chi tiết User do chính mình tạo."""
    return user_admin_service.get_user_for_manager(db, current_manager.id, user_id)


@router.patch("/{user_id}/status", response_model=UserResponse)
def change_managed_user_status(
    user_id: int,
    data: UserStatusRequest,
    db: Session = Depends(get_db),
    current_manager: User = Depends(require_role("manager")),
) -> User:
    """Manager suspend hoặc activate tài khoản Nông dân do chính mình tạo."""
    return user_admin_service.set_managed_user_status(
        db,
        manager=current_manager,
        user_id=user_id,
        data=data,
    )


@router.post("/{user_id}/reset-password", response_model=UserResponse)
def reset_managed_user_password(
    user_id: int,
    data: ManagerResetPasswordRequest,
    db: Session = Depends(get_db),
    current_manager: User = Depends(require_role("manager")),
) -> User:
    """Manager đặt lại mật khẩu cho Nông dân do chính mình tạo."""
    return user_admin_service.reset_managed_user_password(
        db,
        manager=current_manager,
        user_id=user_id,
        new_password=data.new_password,
    )
