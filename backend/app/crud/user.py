"""Module chứa các hàm thao tác trực tiếp với CSDL cho bảng users."""

from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Lấy thông tin người dùng dựa theo username."""
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Lấy thông tin người dùng dựa theo email."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Lấy thông tin người dùng dựa theo id."""
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, user_in: UserCreate) -> User:
    """Tạo mới một người dùng trong cơ sở dữ liệu."""
    email_value = str(user_in.email) if user_in.email is not None else ""
    db_user = User(
        username=user_in.username,
        email=email_value,
        password_hash=hash_password(user_in.password),
        role="user",
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user