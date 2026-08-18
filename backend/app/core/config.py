"""Cấu hình ứng dụng, đọc giá trị từ file .env."""

from pathlib import Path
from typing import List

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
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    MODEL_PATH: str = str(BASE_DIR / "app" / "ml_assets" / "best_model.pt")
    CLASSES_PATH: str = str(BASE_DIR / "app" / "ml_assets" / "classes.json")
    CONFIDENCE_THRESHOLD: float = 0.5  # ngưỡng OOD

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
