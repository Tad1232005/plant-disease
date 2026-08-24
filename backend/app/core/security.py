"""Module chứa các hàm tiện ích băm mật khẩu và xử lý JWT token."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

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
    role: str | None = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Tạo JWT access token cho người dùng."""
    issued_at = datetime.now(timezone.utc)
    expire = issued_at + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: Dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "type": "access",
        "iat": issued_at,
        "jti": uuid4().hex,
    }
    if role is not None:
        payload["role"] = role
    return str(
        jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
    )


def create_refresh_token(subject: str | Any, token_version: int) -> str:
    """Tạo JWT refresh token cho người dùng."""
    issued_at = datetime.now(timezone.utc)
    expire = issued_at + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )
    payload: Dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "type": "refresh",
        "token_version": token_version,
        "iat": issued_at,
        "jti": uuid4().hex,
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
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_TOKEN_INVALID,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
