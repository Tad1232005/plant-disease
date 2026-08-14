"""Module chứa các dependencies xử lý xác thực người dùng và RBAC."""

from collections.abc import Callable
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.crud.user import get_user_by_id
from app.db.session import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Xác thực JWT Access Token và trả về user hiện tại."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực thông tin tài khoản",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)

    if payload.get("type") != "access":
        raise credentials_exception

    subject: Optional[str] = payload.get("sub")
    if subject is None:
        raise credentials_exception

    if str(subject).isdigit():
        user = get_user_by_id(db, int(subject))
    else:
        user = (
            db.query(User)
            .filter(User.username == str(subject))
            .first()
        )

    if user is None:
        raise credentials_exception

    return user


def require_role(*allowed_roles: str) -> Callable[..., User]:
    """Dependency kiểm tra vai trò (RBAC) của người dùng."""

    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền thực hiện hành động này",
            )
        return current_user

    return role_checker