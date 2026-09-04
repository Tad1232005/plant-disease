"""Business logic dùng chung khi Admin/Manager cấp tài khoản."""

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.crud import user as user_crud
from app.models.user import User
from app.schemas.user import AdminCreateUserRequest, ManagerCreateUserRequest

ProvisionRequest = AdminCreateUserRequest | ManagerCreateUserRequest


def create_user_by(
    db: Session,
    *,
    creator: User,
    data: ProvisionRequest,
    role: str,
) -> User:
    """Tạo user có ``created_by`` và role do service quyết định."""
    if role not in {"user", "technician", "manager"}:
        raise ValueError(f"Role cấp tài khoản không hợp lệ: {role}")

    if user_crud.get_user_by_username(db, data.username) is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username đã tồn tại trên hệ thống",
        )

    email_value = str(data.email) if data.email is not None else None
    if email_value and user_crud.get_user_by_email(db, email_value) is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email đã được đăng ký trên hệ thống",
        )

    user = User(
        username=data.username,
        email=email_value,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role=role,
        created_by=creator.id,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username hoặc email đã tồn tại trên hệ thống",
        ) from exc
    db.refresh(user)
    return user


def list_users_for_admin(
    db: Session,
    *,
    role: str | None,
) -> list[User]:
    """Admin xem danh sách tài khoản hệ thống, có thể lọc role."""
    return user_crud.get_users(db, role=role)


def list_managed_users(db: Session, *, manager_id: int) -> list[User]:
    """Manager chỉ xem các User do chính mình tạo."""
    return user_crud.get_users(db, role="user", created_by=manager_id)
