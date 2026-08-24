"""SQLAlchemy Model cho Bảng Users."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
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
    )

    username: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    email: Mapped[Optional[str]] = mapped_column(
        String(100),
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

    created_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    token_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
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
        Index("idx_users_role", "role"),
        Index("idx_users_created_by", "created_by"),
        # Giữ tên index khớp migration ban đầu để Alembic không hiểu nhầm
        # unique index hiện có thành UniqueConstraint mới.
        Index("ix_users_username", "username", unique=True),
        Index("ix_users_email", "email", unique=True),
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

    creator: Mapped[Optional["User"]] = relationship(
        "User",
        remote_side="User.id",
        back_populates="created_users",
        foreign_keys=[created_by],
    )

    created_users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="creator",
        foreign_keys=[created_by],
    )
