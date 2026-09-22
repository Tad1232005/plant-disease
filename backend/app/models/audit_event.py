"""Append-only application audit; never store credentials or image contents."""

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(80))
    resource_type: Mapped[str] = mapped_column(String(50))
    resource_id: Mapped[str] = mapped_column(String(100))
    outcome: Mapped[str] = mapped_column(String(20), default="success", server_default="success")
    details: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        Index("idx_audit_created_at", "created_at"),
        Index("idx_audit_resource", "resource_type", "resource_id", "created_at"),
    )
