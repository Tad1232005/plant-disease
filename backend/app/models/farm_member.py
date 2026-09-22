"""SQLAlchemy model liên kết Managed User với Farm."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.farm import Farm
    from app.models.user import User


class FarmMember(Base):
    """Một User được Manager phân công vào một Farm."""

    __tablename__ = "farm_members"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    farm_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    added_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),  # pylint: disable=not-callable
    )

    __table_args__ = (
        UniqueConstraint(
            "farm_id",
            "user_id",
            name="uq_farm_members_farm_user",
        ),
    )

    farm: Mapped["Farm"] = relationship("Farm", back_populates="members")
    user: Mapped["User"] = relationship(
        "User",
        back_populates="farm_memberships",
        foreign_keys=[user_id],
    )
