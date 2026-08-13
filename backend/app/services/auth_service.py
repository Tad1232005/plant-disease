"""Module chứa logic nghiệp vụ xử lý xác thực và đăng ký người dùng."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
)
from app.crud.user import create_user, get_user_by_email, get_user_by_username
from app.models.user import User
from app.schemas.user import UserCreate


def register_user(db: Session, user_in: UserCreate) -> User:
    """Đăng ký người dùng mới và kiểm tra trùng lặp username/email."""
    if get_user_by_username(db, user_in.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username đã tồn tại trên hệ thống",
        )

    if user_in.email and get_user_by_email(db, str(user_in.email)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email đã được đăng ký trên hệ thống",
        )

    return create_user(db, user_in)


def authenticate_user(
    db: Session,
    username: str,
    password: str,
) -> tuple[str, str, User]:
    """Xác thực thông tin đăng nhập và khởi tạo cặp token."""
    user = get_user_by_username(db, username)
    if user is None:
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

    access_token = create_access_token(user.username)
    refresh_token = create_refresh_token(user.username)

    return access_token, refresh_token, user
