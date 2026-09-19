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
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.farm import Farm
    from app.models.scan_topk import ScanTopK
    from app.models.model_version import ModelVersion
    from app.models.scan_model_result import ScanModelResult


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # Guest KHÔNG lưu vào DB -> user_id bắt buộc NOT NULL
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    farm_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("farms.id", ondelete="SET NULL"),
        nullable=True,
    )

    image_path: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Liên kết LOGIC (không Foreign Key) với disease_info.label_key
    predicted_label: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
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
        String(50),
        nullable=True,
    )

    # FK mới thay cho liên kết chuỗi legacy ở trên. Cột cũ được giữ trong giai
    # đoạn chuyển tiếp để đọc lịch sử scan đã tồn tại.
    primary_model_version_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("model_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    inference_mode: Mapped[str] = mapped_column(
        String(20), nullable=False, default="legacy", server_default="legacy"
    )
    validation_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="accepted", server_default="accepted"
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    agreement_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="single_model", server_default="single_model"
    )
    top1_top2_margin: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ensemble_entropy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    js_divergence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    energy_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ood_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    policy_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    prediction_context: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # Keep the already-applied a7 revision compatible with this checkout.
    inference_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),  # pylint: disable=not-callable
    )

    __table_args__ = (
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_scans_confidence",
        ),
        CheckConstraint(
            "inference_mode IN ('legacy', 'basic', 'standard', 'advanced')",
            name="ck_scans_inference_mode",
        ),
        CheckConstraint(
            "validation_status IN ('accepted', 'low_confidence', 'ambiguous', 'model_error')",
            name="ck_scans_validation_status",
        ),
        CheckConstraint(
            "agreement_status IN ('single_model', 'agreed', 'disagreed', 'degraded')",
            name="ck_scans_agreement_status",
        ),
        CheckConstraint(
            "top1_top2_margin IS NULL OR (top1_top2_margin >= 0 AND top1_top2_margin <= 1)",
            name="ck_scans_margin",
        ),
        CheckConstraint(
            "ensemble_entropy IS NULL OR (ensemble_entropy >= 0 AND ensemble_entropy <= 1)",
            name="ck_scans_entropy",
        ),
        CheckConstraint(
            "js_divergence IS NULL OR (js_divergence >= 0 AND js_divergence <= 1)",
            name="ck_scans_js_divergence",
        ),
        CheckConstraint(
            "ood_score IS NULL OR (ood_score >= 0 AND ood_score <= 1)",
            name="ck_scans_ood_score",
        ),
        Index("idx_scans_user_id", "user_id"),
        Index("idx_scans_farm_id", "farm_id"),
        Index("idx_scans_created_at", "created_at"),
        Index("idx_scans_predicted_label", "predicted_label"),
        Index("idx_scans_primary_model_version_id", "primary_model_version_id"),
        Index("idx_scans_inference_mode", "inference_mode"),
        Index("idx_scans_validation_status", "validation_status"),
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
    primary_model_version: Mapped[Optional["ModelVersion"]] = relationship(
        "ModelVersion", back_populates="primary_scans"
    )
    model_results: Mapped[List["ScanModelResult"]] = relationship(
        "ScanModelResult",
        back_populates="scan",
        cascade="all, delete-orphan",
    )
