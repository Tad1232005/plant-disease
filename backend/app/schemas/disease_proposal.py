from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.disease_info import DiseaseInfoCreate

ProposalStatus = Literal["pending", "approved", "rejected"]


class ProposalCreate(DiseaseInfoCreate):
    base_content_version: int = Field(ge=1)


class ProposalResponse(ProposalCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    proposer_id: int
    proposal_type: Literal["update_content"]
    status: ProposalStatus
    reviewer_id: int | None
    review_note: str | None
    created_at: datetime
    reviewed_at: datetime | None


class RejectProposalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    review_note: str = Field(min_length=1, max_length=2000)
