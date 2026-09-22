"""SQLAlchemy Model cho Bảng DiseaseInfo."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Index,
    String,
    Text,
    true,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class DiseaseInfo(Base):
    __tablename__ = "disease_info"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    label_key: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )

    disease_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    treatment: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    severity_level: Mapped[str] = mapped_column(
        String(20),
        default="medium",
    )

    updated_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),  # pylint: disable=not-callable
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),  # pylint: disable=not-callable
        onupdate=func.now(),        # pylint: disable=not-callable
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=true(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("content_version >= 1", name="ck_disease_info_content_version"),
        CheckConstraint(
            "severity_level IN ('low', 'medium', 'high')",
            name="ck_disease_info_severity_level",
        ),
        Index("idx_disease_info_is_active", "is_active"),
    )

    # Relationship tới User đã cập nhật (nullable)
    content_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )

    updater: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="updated_diseases",
    )
