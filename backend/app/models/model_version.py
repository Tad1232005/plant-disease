"""Phiên bản artifact ML; mỗi kiến trúc có tối đa một version active."""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, Float, Index, Integer, String,
    func, text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.scan import Scan
    from app.models.scan_model_result import ScanModelResult


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version_name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    model_type: Mapped[str] = mapped_column(String(30), nullable=False)
    task: Mapped[str] = mapped_column(
        String(40), nullable=False, default="disease_classification",
        server_default="disease_classification",
    )
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    classes_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    temperature_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    temperature: Mapped[float] = mapped_column(
        Float, nullable=False, default=1.0, server_default="1.0"
    )
    sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    macro_f1: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ece: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    metrics_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="1"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "model_type IN ('mobilenet_v2', 'efficientnet_b0', 'resnet50')",
            name="ck_model_versions_model_type",
        ),
        CheckConstraint("temperature > 0", name="ck_model_versions_temperature"),
        CheckConstraint(
            "accuracy IS NULL OR (accuracy >= 0 AND accuracy <= 1)",
            name="ck_model_versions_accuracy",
        ),
        CheckConstraint(
            "macro_f1 IS NULL OR (macro_f1 >= 0 AND macro_f1 <= 1)",
            name="ck_model_versions_macro_f1",
        ),
        CheckConstraint(
            "ece IS NULL OR (ece >= 0 AND ece <= 1)",
            name="ck_model_versions_ece",
        ),
        Index("idx_model_versions_model_type", "model_type"),
        Index("idx_model_versions_is_enabled", "is_enabled"),
        Index(
            "idx_one_active_version_per_model_type",
            "model_type",
            unique=True,
            postgresql_where=text("is_active = true"),
            sqlite_where=text("is_active = 1"),
        ),
    )

    primary_scans: Mapped[List["Scan"]] = relationship(
        "Scan", back_populates="primary_model_version"
    )
    scan_results: Mapped[List["ScanModelResult"]] = relationship(
        "ScanModelResult", back_populates="model_version"
    )
