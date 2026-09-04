"""Schema cho inference nhiều model và capability theo role."""

from typing import Literal, Optional

from pydantic import BaseModel, Field

InferenceMode = Literal["basic", "standard", "advanced"]
RequestedMode = Literal["auto", "basic", "standard", "advanced"]
ValidationStatus = Literal["accepted", "low_confidence", "ambiguous", "model_error"]
AgreementStatus = Literal["single_model", "agreed", "disagreed", "degraded"]


class TopKResult(BaseModel):
    label: str = Field(..., description="Nhãn trong bộ 38 classes")
    confidence: float = Field(..., ge=0, le=1)
    rank: int = Field(..., ge=1, le=3)


class ModelPredictionResponse(BaseModel):
    model_version_id: int
    version_name: str
    model_type: Literal["mobilenet_v2", "efficientnet_b0", "resnet50"]
    execution_order: int = Field(..., ge=1, le=3)
    predicted_label: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    top1_top2_margin: Optional[float] = Field(default=None, ge=0, le=1)
    entropy: Optional[float] = Field(default=None, ge=0, le=1)
    energy_score: Optional[float] = None
    accepted: bool
    latency_ms: Optional[float] = Field(default=None, ge=0)
    error_code: Optional[str] = None
    top_k: list[TopKResult] = Field(default_factory=list)


FarmAssignmentStatus = Literal[
    "not_applicable", "not_requested", "assigned", "not_allowed"
]


class PredictResponse(BaseModel):
    # label=None nghĩa là policy từ chối chẩn đoán; top_k vẫn giữ để audit.
    label: Optional[str] = None
    confidence: float = Field(..., ge=0, le=1)
    is_valid_leaf: bool
    top_k: list[TopKResult]
    model_version: str = Field(..., description="Primary version (legacy compatibility)")
    inference_mode: InferenceMode
    validation_status: ValidationStatus
    rejection_reason: Optional[str] = None
    agreement_status: AgreementStatus
    agreement_count: int = Field(..., ge=0, le=3)
    models_requested: int = Field(..., ge=1, le=3)
    models_succeeded: int = Field(..., ge=1, le=3)
    top1_top2_margin: float = Field(..., ge=0, le=1)
    ensemble_entropy: float = Field(..., ge=0, le=1)
    js_divergence: float = Field(..., ge=0, le=1)
    energy_score: float
    ood_score: float = Field(..., ge=0, le=1)
    policy_version: str
    model_results: list[ModelPredictionResponse]
    scan_id: Optional[int] = None
    farm_id: Optional[int] = None
    farm_assignment_status: FarmAssignmentStatus
    warning: Optional[str] = None
    disease_name: Optional[str] = None
    description: Optional[str] = None
    treatment: Optional[str] = None
    severity_level: Optional[Literal["low", "medium", "high"]] = None


class PredictCapabilitiesResponse(BaseModel):
    role: Literal["guest", "user", "manager", "technician", "admin"]
    default_mode: InferenceMode
    allowed_modes: list[InferenceMode]
    models_by_mode: dict[str, list[str]]
    policy_version: str
