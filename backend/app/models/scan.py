"""SQLAlchemy Model cho Bảng Scans (Bảng Trung Tâm)."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.farm import Farm
    from app.models.scan_topk import ScanTopK


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
    )

    # Guest KHÔNG lưu vào DB -> user_id bắt buộc NOT NULL
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    farm_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("farms.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    image_path: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Liên kết LOGIC (không Foreign Key) với disease_info.label_key
    predicted_label: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    confidence: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    is_valid_leaf: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    gradcam_path: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Liên kết LOGIC (không Foreign Key) với model_versions.version_name
    model_version: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),  # pylint: disable=not-callable
        index=True,
    )

    __table_args__ = (
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_scans_confidence",
        ),
        Index("idx_scans_user_id", "user_id"),
        Index("idx_scans_farm_id", "farm_id"),
        Index("idx_scans_created_at", "created_at"),
        Index("idx_scans_predicted_label", "predicted_label"),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="scans")
    farm: Mapped[Optional["Farm"]] = relationship(
        "Farm", back_populates="scans"
    )
    topk_results: Mapped[List["ScanTopK"]] = relationship(
        "ScanTopK",
        back_populates="scan",
        cascade="all, delete-orphan",
    )
