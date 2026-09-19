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
from app.api.auth_origin import require_trusted_auth_origin
from app.api.auth_rate_limit import require_auth_rate_limit
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest, LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import (
    authenticate_user,
    refresh_access_token,
    register_user,
    revoke_refresh_tokens,
    change_password,
)

router = APIRouter(prefix="/auth", tags=["Auth"], dependencies=[
    Depends(require_trusted_auth_origin), Depends(require_auth_rate_limit),
])


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_my_password(
    data: ChangePasswordRequest,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    change_password(db, current_user, data.current_password, data.new_password)
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME, path=settings.REFRESH_COOKIE_PATH,
        secure=settings.COOKIE_SECURE, httponly=True, samesite=settings.COOKIE_SAMESITE,
    )


def _set_refresh_cookie(response: Response, token: str) -> None:
    """Thiết lập refresh token theo cấu hình bảo mật dùng chung."""
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path=settings.REFRESH_COOKIE_PATH,
    )


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
    _set_refresh_cookie(response, refresh_token)
    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Tạo Access Token mới từ Refresh Token trong Cookie."""
    refresh_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing in cookies",
        )

    new_access_token, new_refresh_token = refresh_access_token(
        db, refresh_token)
    _set_refresh_cookie(response, new_refresh_token)
    return TokenResponse(access_token=new_access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Đăng xuất và vô hiệu hóa toàn bộ refresh token đang còn hiệu lực."""
    revoke_refresh_tokens(db, current_user)
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        path=settings.REFRESH_COOKIE_PATH,
        secure=settings.COOKIE_SECURE,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
    )


@router.get("/me", response_model=UserResponse)
def me(
    current_user: User = Depends(get_current_user),
) -> User:
    """Endpoint lấy thông tin người dùng đang đăng nhập."""
    return current_user
