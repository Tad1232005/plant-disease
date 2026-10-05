"""Core application exceptions."""

from app.services.predict_service import (
    InferenceCapacityError,
    ModeNotAllowedError,
    ModelConfigurationError,
)

__all__ = [
    "InferenceCapacityError",
    "ModeNotAllowedError",
    "ModelConfigurationError",
]
