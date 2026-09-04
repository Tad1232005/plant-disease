"""API Manager quản lý Managed User của chính mình."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import ManagerCreateUserRequest, UserResponse
from app.services import user_admin_service

router = APIRouter(prefix="/manager/users", tags=["Manager Users"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
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
    db: Session = Depends(get_db),
    current_manager: User = Depends(require_role("manager")),
) -> list[User]:
    """Manager chỉ xem User do chính mình tạo."""
    return user_admin_service.list_managed_users(
        db,
        manager_id=current_manager.id,
    )
