"""SQLAlchemy Model cho Bảng ScanTopK."""

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.scan import Scan


class ScanTopK(Base):
    __tablename__ = "scan_topk"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True,
    )

    scan_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    label: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    rank: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_scan_topk_confidence",
        ),
        CheckConstraint(
            "rank BETWEEN 1 AND 3",
            name="ck_scan_topk_rank",
        ),
    )

    # Relationship tới Scan (back_populates phải khớp với bên Scan)
    scan: Mapped["Scan"] = relationship(
        "Scan",
        back_populates="topk_results",
    )
