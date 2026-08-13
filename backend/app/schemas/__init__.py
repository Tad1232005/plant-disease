from pydantic import BaseModel

from app.schemas.user import UserCreate, UserResponse


class PredictResponse(BaseModel):
    label: str
    confidence: float


__all__ = ["PredictResponse", "UserCreate", "UserResponse"]
