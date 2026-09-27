"""Module chứa logic nghiệp vụ xử lý xác thực và đăng ký người dùng."""

from typing import Tuple

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
    hash_password,
)
from app.crud.user import create_user, get_user_by_email, get_user_by_username
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.audit_service import record_event


def change_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    """Atomically replace the hash and invalidate all issued tokens."""
    if not verify_password(current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Mật khẩu hiện tại không đúng")
    if current_password == new_password:
        raise HTTPException(status_code=400, detail="Mật khẩu mới phải khác mật khẩu cũ")
    result = db.execute(
        update(User).where(
            User.id == user.id,
            User.password_hash == user.password_hash,
            User.token_version == user.token_version,
        ).values(password_hash=hash_password(new_password), token_version=User.token_version + 1).returning(User.id),
        execution_options={"synchronize_session": False},
    )
    if result.scalar_one_or_none() is None:
        db.rollback()
        raise HTTPException(status_code=409, detail="Tài khoản vừa thay đổi; hãy đăng nhập lại")
    record_event(db, actor_id=user.id, action="user.password_changed", resource_type="user",
                 resource_id=user.id, details={})
    db.commit()
    db.refresh(user)


def register_user(db: Session, user_in: UserCreate) -> User:
    """Đăng ký người dùng mới và kiểm tra trùng lặp username/email."""
    if get_user_by_username(db, user_in.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username đã tồn tại trên hệ thống",
        )

    if user_in.email and get_user_by_email(db, str(user_in.email)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email đã được đăng ký trên hệ thống",
        )

    try:
        return create_user(db, user_in)
    except IntegrityError as exc:
        # Chặn race giữa bước kiểm tra trùng và unique constraint lúc commit.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username hoặc email đã tồn tại trên hệ thống",
        ) from exc


def authenticate_user(
    db: Session,
    username: str,
    password: str,
) -> Tuple[str, str, User]:
    """Xác thực thông tin đăng nhập và khởi tạo cặp token."""
    user = get_user_by_username(db, username)
    if user is None or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sai tên đăng nhập hoặc mật khẩu",
        )

    stored_hash = user.password_hash
    if not isinstance(stored_hash, str):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Dữ liệu password không hợp lệ",
        )

    if not verify_password(password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sai tên đăng nhập hoặc mật khẩu",
        )

    access_token = create_access_token(
        user.id,
        role=user.role,
        token_version=user.token_version,
    )
    refresh_token = create_refresh_token(user.id, user.token_version)

    return access_token, refresh_token, user


def refresh_access_token(db: Session, refresh_token: str) -> Tuple[str, str]:
    """Xác thực refresh cookie và cấp một cặp token mới."""
    payload = decode_token(refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token type không hợp lệ",
        )

    subject = payload.get("sub")
    token_version = payload.get("token_version")
    if (
        not subject
        or not isinstance(token_version, int)
        or isinstance(token_version, bool)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token thiếu thông tin người dùng",
        )

    try:
        user_id = int(subject)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token thiếu thông tin người dùng",
        ) from exc

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Người dùng không tồn tại",
        )

    if user.status != "active" or user.token_version != token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token đã hết hiệu lực",
        )

    return (
        create_access_token(
            user.id,
            role=user.role,
            token_version=user.token_version,
        ),
        create_refresh_token(user.id, user.token_version),
    )


def revoke_refresh_tokens(db: Session, user: User) -> None:
    """Vô hiệu hóa toàn bộ access/refresh token đã phát hành của user."""
    db.execute(update(User).where(User.id == user.id).values(token_version=User.token_version + 1))
    db.commit()
