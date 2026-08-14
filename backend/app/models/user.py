"""SQLAlchemy Model cho Bảng Users."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.farm import Farm
    from app.models.scan import Scan
    from app.models.disease_info import DiseaseInfo


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
    )

    username: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )

    email: Mapped[Optional[str]] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="user",
    )

    full_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),  # pylint: disable=not-callable
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'technician', 'manager', 'admin')",
            name="ck_users_role",
        ),
    )

    # Relationships
    farms: Mapped[List["Farm"]] = relationship(
        "Farm",
        back_populates="owner",
        cascade="all, delete-orphan",
    )

    scans: Mapped[List["Scan"]] = relationship(
        "Scan",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    updated_diseases: Mapped[List["DiseaseInfo"]] = relationship(
        "DiseaseInfo",
        back_populates="updater",
    )
