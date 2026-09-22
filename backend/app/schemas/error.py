from typing import Any
from pydantic import BaseModel


class ApiError(BaseModel):
    # Existing HTTPException strings and FastAPI validation lists are preserved.
    detail: str | list[dict[str, Any]]
