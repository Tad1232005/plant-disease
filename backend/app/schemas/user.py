from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """Schema dùng khi người dùng đăng ký tài khoản."""

    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    password: str = Field(..., min_length=6, max_length=128)
    full_name: Optional[str] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        """Đảm bảo username có độ dài hợp lệ."""
        if len(value.strip()) < 3:
            raise ValueError("Username phải có ít nhất 3 ký tự")
        return value.strip()

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        """Đảm bảo password có độ dài tối thiểu."""
        if len(value) < 6:
            raise ValueError("Password phải có ít nhất 6 ký tự")
        return value


class UserResponse(BaseModel):
    """Schema trả về dữ liệu người dùng công khai."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: Optional[str] = None
    role: str
    full_name: Optional[str] = None
