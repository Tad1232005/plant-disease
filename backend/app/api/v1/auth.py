"""Module định nghĩa các API Endpoints cho việc xác thực người dùng."""

from typing import Dict

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import (
    authenticate_user,
    refresh_access_token,
    register_user,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db),
) -> User:
    """Endpoint đăng ký tài khoản người dùng mới."""
    return register_user(db, user_in)


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Endpoint đăng nhập và thiết lập Refresh Token trong HttpOnly Cookie."""
    access_token, refresh_token, _ = authenticate_user(
        db,
        form_data.username,
        form_data.password,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=7 * 24 * 60 * 60,
        samesite="lax",
        path="/api/v1/auth/refresh",
    )
    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Tạo Access Token mới từ Refresh Token trong Cookie."""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing in cookies",
        )

    new_access_token = refresh_access_token(db, refresh_token)
    return TokenResponse(access_token=new_access_token)


@router.post("/logout")
def logout(response: Response) -> Dict[str, str]:
    """Endpoint đăng xuất, xóa Refresh Token khỏi Cookie."""
    response.delete_cookie(
        key="refresh_token",
        path="/api/v1/auth/refresh",
    )
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def me(
    current_user: User = Depends(get_current_user),
) -> User:
    """Endpoint lấy thông tin người dùng đang đăng nhập."""
    return current_user
