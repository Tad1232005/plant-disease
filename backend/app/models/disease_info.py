"""SQLAlchemy Model cho Bảng DiseaseInfo."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
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
        index=True,
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

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),  # pylint: disable=not-callable
        onupdate=func.now(),        # pylint: disable=not-callable
    )

    __table_args__ = (
        CheckConstraint(
            "severity_level IN ('low', 'medium', 'high')",
            name="ck_disease_info_severity_level",
        ),
    )

    # Relationship tới User đã cập nhật (nullable)
    updater: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="updated_diseases",
    )
