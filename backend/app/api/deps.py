"""Module chứa các dependencies xử lý xác thực người dùng và RBAC."""

from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.crud.user import get_user_by_id, get_user_by_username
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

    try:
        payload = decode_token(token)
    except Exception as exc:
        raise credentials_exception from exc

    if payload.get("type") != "access":
        raise credentials_exception

    subject: str | None = payload.get("sub")
    if not subject:
        raise credentials_exception

    # Gọi qua CRUD Layer thay vì query DB trực tiếp
    if subject.isdigit():
        user = get_user_by_id(db, int(subject))
    else:
        user = get_user_by_username(db, subject)

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
