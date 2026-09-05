"""Kết quả riêng của từng model tham gia một lượt scan."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, false,
    String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.model_version import ModelVersion
    from app.models.scan import Scan


class ScanModelResult(Base):
    __tablename__ = "scan_model_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("scans.id", ondelete="CASCADE"), nullable=False
    )
    model_version_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("model_versions.id", ondelete="RESTRICT"), nullable=False
    )
    execution_order: Mapped[int] = mapped_column(Integer, nullable=False)
    predicted_label: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    top1_top2_margin: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    entropy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    energy_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    accepted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    topk_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "scan_id", "model_version_id", name="uq_scan_model_result_model"
        ),
        CheckConstraint("execution_order BETWEEN 1 AND 3", name="ck_scan_model_result_order"),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_scan_model_result_confidence",
        ),
        CheckConstraint(
            "top1_top2_margin IS NULL OR (top1_top2_margin >= 0 AND top1_top2_margin <= 1)",
            name="ck_scan_model_result_margin",
        ),
        CheckConstraint(
            "entropy IS NULL OR (entropy >= 0 AND entropy <= 1)",
            name="ck_scan_model_result_entropy",
        ),
        CheckConstraint(
            "latency_ms IS NULL OR latency_ms >= 0",
            name="ck_scan_model_result_latency",
        ),
        Index("idx_scan_model_results_scan_id", "scan_id"),
        Index("idx_scan_model_results_model_version_id", "model_version_id"),
        Index("idx_scan_model_results_created_at", "created_at"),
    )

    scan: Mapped["Scan"] = relationship("Scan", back_populates="model_results")
    model_version: Mapped["ModelVersion"] = relationship(
        "ModelVersion", back_populates="scan_results"
    )
