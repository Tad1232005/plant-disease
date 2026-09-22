"""SQLAlchemy Model cho Bảng Farms."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.farm_member import FarmMember
    from app.models.user import User
    from app.models.scan import Scan


class Farm(Base):
    __tablename__ = "farms"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    owner_id: Mapped[int] = mapped_column(
        "user_id",
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    location_text: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),  # pylint: disable=not-callable
    )

    # Relationships
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="farms",
    )

    scans: Mapped[List["Scan"]] = relationship(
        "Scan",
        back_populates="farm",
    )

    archived_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    __table_args__ = (Index("idx_farms_archived_at", "archived_at"),)

    members: Mapped[List["FarmMember"]] = relationship(
        "FarmMember",
        back_populates="farm",
        cascade="all, delete-orphan",
    )
