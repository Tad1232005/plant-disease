"""Schemas cho lịch sử và chi tiết chẩn đoán."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.predict import AgreementStatus, InferenceMode, ValidationStatus


class ScanHistoryItem(BaseModel):
    """Một dòng trong lịch sử scan của user hiện tại."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    farm_id: Optional[int] = None
    image_path: str
    predicted_label: Optional[str] = None
    confidence: Optional[float] = None
    is_valid_leaf: bool
    model_version: Optional[str] = None
    inference_mode: str
    validation_status: ValidationStatus
    agreement_status: AgreementStatus
    created_at: datetime


class ScanTopKItem(BaseModel):
    """Một kết quả trong top-3 dự đoán."""

    model_config = ConfigDict(from_attributes=True)

    label: str
    confidence: float
    rank: int

class ScanModelResultItem(BaseModel):
    """Audit của một model trong ensemble."""

    model_version_id: int
    version_name: str
    model_type: str
    execution_order: int
    predicted_label: Optional[str] = None
    confidence: Optional[float] = None
    top1_top2_margin: Optional[float] = None
    entropy: Optional[float] = None
    energy_score: Optional[float] = None
    accepted: bool
    latency_ms: Optional[float] = None
    error_code: Optional[str] = None
    top_k: list[ScanTopKItem] = Field(default_factory=list)


class ScanDetailResponse(BaseModel):
    """Chi tiết một scan, thông tin bệnh và top-3 dự đoán."""

    id: int
    user_id: int
    farm_id: Optional[int] = None
    image_path: str
    predicted_label: Optional[str] = None
    confidence: Optional[float] = None
    is_valid_leaf: bool
    gradcam_path: Optional[str] = None
    model_version: Optional[str] = None
    primary_model_version_id: Optional[int] = None
    inference_mode: str
    validation_status: ValidationStatus
    rejection_reason: Optional[str] = None
    agreement_status: AgreementStatus
    top1_top2_margin: Optional[float] = None
    ensemble_entropy: Optional[float] = None
    js_divergence: Optional[float] = None
    energy_score: Optional[float] = None
    ood_score: Optional[float] = None
    policy_version: Optional[str] = None
    created_at: datetime
    disease_name: Optional[str] = None
    treatment: Optional[str] = None
    top3: list[ScanTopKItem] = Field(default_factory=list)
    model_results: list[ScanModelResultItem] = Field(default_factory=list)
