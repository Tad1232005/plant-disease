"""Generic pagination schemas for API responses."""

from typing import Generic, Sequence, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic wrapper for paginated endpoints that use body encapsulation."""

    model_config = ConfigDict(from_attributes=True)

    items: Sequence[T] = Field(default_factory=list, description="Danh sách các bản ghi của trang hiện tại")
    total: int = Field(ge=0, description="Tổng số bản ghi thỏa mãn điều kiện lọc")
    limit: int = Field(ge=1, description="Số lượng bản ghi tối đa mỗi trang")
    offset: int = Field(ge=0, description="Vị trí bắt đầu của trang hiện tại")

    @property
    def has_more(self) -> bool:
        """Kiểm tra xem còn trang kế tiếp hay không."""
        return self.offset + len(self.items) < self.total
