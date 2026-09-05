"""Cấu hình ứng dụng, đọc giá trị từ file .env."""

from pathlib import Path
from typing import List, Literal, Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Lớp chứa toàn bộ biến cấu hình của ứng dụng."""

    PROJECT_NAME: str = "Plant Disease API"
    API_V1_STR: str = "/api/v1"
    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_PORT: int = 55432
    POSTGRES_DB: str = "plant_disease"
    POSTGRES_USER: str = "plant_app"
    POSTGRES_PASSWORD: str = ""
    DATABASE_URL: str = ""
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REFRESH_COOKIE_NAME: str = "refresh_token"
    REFRESH_COOKIE_PATH: str = "/api/v1/auth"
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    MODEL_ARTIFACT_ROOT: str = str(BASE_DIR / "app" / "ml_assets" / "models")
    CONFIDENCE_THRESHOLD: float = 0.3
    TOP1_MARGIN_THRESHOLD: float = 0.05
    JS_DIVERGENCE_THRESHOLD: float = 0.3
    PARALLEL_MODEL_INFERENCE: bool = True
    MAX_CONCURRENT_INFERENCES: int = 1
    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024
    MAX_IMAGE_PIXELS: int = 20_000_000
    INFERENCE_TIMEOUT_SECONDS: float = 30.0
    UPLOAD_DIR: str = str(BASE_DIR / "storage" / "uploads")
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT_SECONDS: int = 30

    @model_validator(mode="after")
    def configure_database_url(self) -> Self:
        """Tạo URL an toàn từ POSTGRES_* hoặc kiểm tra URL override."""
        if self.DATABASE_URL:
            if not self.DATABASE_URL.startswith("postgresql+psycopg://"):
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

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
