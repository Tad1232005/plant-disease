from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

UserRole = Literal["user", "technician", "manager", "admin"]
UserStatus = Literal["active", "suspended"]


class UserStatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    status: UserStatus
    reason: str = Field(min_length=1, max_length=1000)


class UserCreate(BaseModel):
    """Schema dùng khi người dùng đăng ký tài khoản."""

    model_config = ConfigDict(extra="forbid")

    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(default=None, max_length=100)

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
        if len(value) < 8:
            raise ValueError("Password phải có ít nhất 8 ký tự")
        if not any(char.islower() for char in value):
            raise ValueError("Password phải có chữ thường")
        if not any(char.isupper() for char in value):
            raise ValueError("Password phải có chữ hoa")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password phải có chữ số")
        return value


class UserResponse(BaseModel):
    """Schema trả về dữ liệu người dùng công khai."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: Optional[str] = None
    role: str
    status: UserStatus
    full_name: Optional[str] = None
    created_by: Optional[int] = None


class _ProvisionUserRequest(BaseModel):
    """Các field chung khi Admin/Manager cấp tài khoản."""

    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    password: str = Field(min_length=8, max_length=128)
    full_name: Optional[str] = Field(default=None, max_length=100)

    @field_validator("username")
    @classmethod
    def strip_username(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Username phải có ít nhất 3 ký tự")
        return value

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if not (
            any(char.islower() for char in value)
            and any(char.isupper() for char in value)
            and any(char.isdigit() for char in value)
        ):
            raise ValueError("Password phải có chữ hoa, chữ thường và chữ số")
        return value


class AdminCreateUserRequest(_ProvisionUserRequest):
    """Admin chỉ được cấp tài khoản Technician hoặc Manager."""

    role: str

    @field_validator("role")
    @classmethod
    def validate_admin_created_role(cls, value: str) -> str:
        if value not in {"technician", "manager"}:
            raise ValueError("Admin chỉ được tạo role technician hoặc manager")
        return value


class ManagerCreateUserRequest(_ProvisionUserRequest):
    """Manager tạo Managed User; cố ý không có field role."""
