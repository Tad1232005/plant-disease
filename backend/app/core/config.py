"""Cấu hình ứng dụng, đọc giá trị từ file .env."""

from pathlib import Path
from typing import List, Literal, Self
from urllib.parse import urlsplit

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Lớp chứa toàn bộ biến cấu hình của ứng dụng."""

    PROJECT_NAME: str = "Plant Disease API"
    APP_ENV: Literal["development", "test", "production"] = "development"
    API_V1_STR: str = "/api/v1"
    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_PORT: int = Field(default=55432, ge=1, le=65535)
    POSTGRES_DB: str = "plant_disease"
    POSTGRES_USER: str = "plant_app"
    POSTGRES_PASSWORD: str = Field(default="", repr=False)
    DATABASE_URL: str = Field(default="", repr=False)
    SECRET_KEY: str = Field(default="change-me-in-production", repr=False)
    ALGORITHM: Literal["HS256"] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, gt=0)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, gt=0)
    REFRESH_COOKIE_NAME: str = "refresh_token"
    REFRESH_COOKIE_PATH: str = "/api/v1/auth"
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
    # Set the externally visible API origin to allow Swagger cookie requests.
    PUBLIC_API_ORIGIN: str = "http://127.0.0.1:8000"
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    MODEL_ARTIFACT_ROOT: str = str(BASE_DIR / "app" / "ml_assets" / "models")
    CONFIDENCE_THRESHOLD: float = Field(default=0.3, ge=0, le=1, allow_inf_nan=False)
    TOP1_MARGIN_THRESHOLD: float = Field(default=0.05, ge=0, le=1, allow_inf_nan=False)
    JS_DIVERGENCE_THRESHOLD: float = Field(default=0.3, ge=0, le=1, allow_inf_nan=False)
    PARALLEL_MODEL_INFERENCE: bool = True
    MAX_CONCURRENT_INFERENCES: int = Field(default=1, gt=0)
    MAX_UPLOAD_BYTES: int = Field(default=10 * 1024 * 1024, gt=0)
    MAX_IMAGE_PIXELS: int = Field(default=20_000_000, gt=0)
    INFERENCE_TIMEOUT_SECONDS: float = Field(default=30.0, gt=0, allow_inf_nan=False)
    UPLOAD_DIR: str = str(BASE_DIR / "storage" / "uploads")
    DB_POOL_SIZE: int = Field(default=5, gt=0)
    DB_MAX_OVERFLOW: int = Field(default=10, ge=0)
    DB_POOL_TIMEOUT_SECONDS: int = Field(default=30, gt=0)
    AUTH_RATE_WINDOW_SECONDS: int = Field(default=300, ge=1, le=3600)
    AUTH_LOGIN_RATE_LIMIT: int = Field(default=30, ge=1, le=10000)
    AUTH_REGISTER_RATE_LIMIT: int = Field(default=10, ge=1, le=10000)
    AUTH_REFRESH_RATE_LIMIT: int = Field(default=120, ge=1, le=10000)
    AUTH_PASSWORD_RATE_LIMIT: int = Field(default=10, ge=1, le=10000)

    @model_validator(mode="after")
    def configure_database_url(self) -> Self:
        """Tạo URL an toàn từ POSTGRES_* hoặc kiểm tra URL override."""
        if self.DATABASE_URL:
            if make_url(self.DATABASE_URL).drivername != "postgresql+psycopg":
                raise ValueError("DATABASE_URL phải dùng PostgreSQL với driver psycopg")
            return self
        if not self.POSTGRES_PASSWORD:
            raise ValueError("POSTGRES_PASSWORD không được để trống")
        self.DATABASE_URL = URL.create(
            "postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        ).render_as_string(hide_password=False)
        return self

    @model_validator(mode="after")
    def validate_runtime_security(self) -> Self:
        if self.COOKIE_SAMESITE == "none" and not self.COOKIE_SECURE:
            raise ValueError("COOKIE_SAMESITE=none requires COOKIE_SECURE=true")
        origins = [*self.CORS_ORIGINS, self.PUBLIC_API_ORIGIN]
        for origin in origins:
            parts = urlsplit(origin)
            if (parts.scheme not in {"http", "https"} or not parts.hostname
                    or parts.username is not None or parts.password is not None
                    or parts.path or parts.query or parts.fragment
                    or "*" in origin or any(char.isspace() for char in origin)):
                raise ValueError("Origins must be explicit http(s) origins without paths or credentials")
            # Accessing port also validates malformed/out-of-range ports.
            _ = parts.port
        refresh_path = self.API_V1_STR + "/auth/refresh"
        cookie_path = self.REFRESH_COOKIE_PATH.rstrip("/")
        if not self.REFRESH_COOKIE_PATH.startswith("/") or not (
            refresh_path == self.REFRESH_COOKIE_PATH or refresh_path.startswith(cookie_path + "/")
        ):
            raise ValueError("REFRESH_COOKIE_PATH must cover the auth refresh endpoint")
        if self.APP_ENV == "production":
            weak_markers = ("change", "example", "demo", "password", "secret-key")
            if (len(self.SECRET_KEY.encode("utf-8")) < 32
                    or any(marker in self.SECRET_KEY.lower() for marker in weak_markers)):
                raise ValueError("Production requires a generated SECRET_KEY of at least 32 bytes")
            if not self.COOKIE_SECURE:
                raise ValueError("Production requires COOKIE_SECURE=true")
            if any(urlsplit(origin).scheme != "https" for origin in origins):
                raise ValueError("Production requires HTTPS API/CORS origins")
            password = make_url(self.DATABASE_URL).password
            if not password or password in {"plant_dev_password", "postgres", "password"}:
                raise ValueError("Production requires non-demo database credentials")
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
        hide_input_in_errors=True,
    )


settings = Settings()
