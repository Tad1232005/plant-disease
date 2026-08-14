"""Module định nghĩa các API Endpoints cho việc xác thực người dùng."""

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
from app.core.security import create_access_token, decode_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import authenticate_user, register_user

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
    """Endpoint đăng nhập và thiết lập Refresh Token trong Cookie."""
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
    )
    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Tạo access token mới từ refresh token trong cookie."""
    refresh_token_cookie = request.cookies.get("refresh_token")
    if not refresh_token_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    payload = decode_token(refresh_token_cookie)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token type invalid",
        )

    subject = payload.get("sub")
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject",
        )

    user = (
        db.query(User)
        .filter(User.username == str(subject))
        .first()
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    access_token = create_access_token(user.username)
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
def me(
    current_user: User = Depends(get_current_user),
) -> User:
    """Endpoint lấy thông tin người dùng đang đăng nhập."""
    return current_user