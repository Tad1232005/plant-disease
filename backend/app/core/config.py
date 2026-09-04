"""Cấu hình ứng dụng, đọc giá trị từ file .env."""

from pathlib import Path
from typing import List, Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Lớp chứa toàn bộ biến cấu hình của ứng dụng."""

    PROJECT_NAME: str = "Plant Disease API"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./app.db"
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

    # MODEL_PATH/CLASSES_PATH được giữ để tương thích cấu hình cũ. Inference
    # nhiều model đọc artifact từ MODEL_ARTIFACT_ROOT và metadata trong DB.
    MODEL_PATH: str = str(BASE_DIR / "app" / "ml_assets" / "best_model.pt")
    CLASSES_PATH: str = str(BASE_DIR / "app" / "ml_assets" / "classes.json")
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

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
