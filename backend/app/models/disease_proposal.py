"""Versioned content suggestions, not requests to extend classifier labels."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DiseaseProposal(Base):
    __tablename__ = "disease_proposals"

    id: Mapped[int] = mapped_column(primary_key=True)
    proposer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    label_key: Mapped[str] = mapped_column(String(50), nullable=False)
    proposal_type: Mapped[str] = mapped_column(String(30), default="update_content", server_default="update_content")
    base_content_version: Mapped[int] = mapped_column(Integer)
    disease_name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    treatment: Mapped[str | None] = mapped_column(Text)
    severity_level: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending")
    reviewer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    review_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint("proposal_type = 'update_content'", name="ck_proposals_type"),
        CheckConstraint("base_content_version >= 1", name="ck_proposals_version"),
        CheckConstraint("status IN ('pending', 'approved', 'rejected')", name="ck_proposals_status"),
        CheckConstraint("severity_level IN ('low', 'medium', 'high')", name="ck_proposals_severity"),
        CheckConstraint("(status = 'pending' AND reviewed_at IS NULL AND reviewer_id IS NULL) OR (status <> 'pending' AND reviewed_at IS NOT NULL)", name="ck_proposals_review"),
        CheckConstraint("status <> 'rejected' OR (review_note IS NOT NULL AND length(trim(review_note)) > 0)", name="ck_proposals_reject_note"),
        Index("idx_proposals_mine", "proposer_id", "created_at", "id"),
        Index("idx_proposals_queue", "status", "created_at", "id"),
    )
