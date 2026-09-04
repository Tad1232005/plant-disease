"""Pydantic schemas cho thành viên Farm."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserResponse


class FarmMemberAddRequest(BaseModel):
    """Managed User mà Manager muốn gán vào Farm."""

    model_config = ConfigDict(extra="forbid")

    user_id: int


class FarmMemberResponse(BaseModel):
    """Thông tin một thành viên cùng tài khoản User liên quan."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    farm_id: int
    user_id: int
    added_by: Optional[int] = None
    created_at: datetime
    user: UserResponse
