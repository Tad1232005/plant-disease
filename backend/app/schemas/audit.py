"""Response cho nhật ký kiểm toán (read-only; bảng append-only)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditEventItem(BaseModel):
    """Một sự kiện audit kèm tên người thực hiện (join từ users)."""

    id: int
    actor_id: int | None
    actor_name: str
    action: str
    resource_type: str
    resource_id: str
    outcome: str
    details: dict[str, Any]
    created_at: datetime
