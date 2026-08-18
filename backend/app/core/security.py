"""Module chứa các hàm tiện ích băm mật khẩu và xử lý JWT token."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, cast

from fastapi import HTTPException, status
from jose import JWTError, jwt  # type: ignore[import-untyped]
from passlib.context import CryptContext  # type: ignore[import-untyped]

from app.core.config import settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

_TOKEN_INVALID = "Token không hợp lệ hoặc đã hết hạn"


def hash_password(password: str) -> str:
    """Băm mật khẩu plain-text bằng Argon2."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Xác thực mật khẩu plain-text với hash đã lưu."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: str | Any,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Tạo JWT access token cho người dùng."""
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: Dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "type": "access",
    }
    return str(
        jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
    )


def create_refresh_token(subject: str | Any) -> str:
    """Tạo JWT refresh token cho người dùng."""
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )
    payload: Dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "type": "refresh",
    }
    return str(
        jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
    )


def decode_token(token: str) -> Dict[str, Any]:
    """Giải mã và kiểm tra tính hợp lệ của JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return cast(Dict[str, Any], payload)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_TOKEN_INVALID,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
