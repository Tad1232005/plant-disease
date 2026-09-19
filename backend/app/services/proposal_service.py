"""Atomic, revision-checked content approval with idempotent same-decision retries."""

from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.crud.disease_info import apply_content, lock_disease
from app.models.disease_proposal import DiseaseProposal
from app.models.user import User
from app.schemas.disease_info import DiseaseInfoUpdate
from app.schemas.disease_proposal import ProposalCreate
from app.services.audit_service import record_event


def submit(db: Session, actor: User, data: ProposalCreate) -> DiseaseProposal:
    content = lock_disease(db, data.label_key)
    if content is None or not content.is_active:
        raise HTTPException(status_code=404, detail="Chỉ được đề xuất sửa nhãn đang tồn tại")
    if content.content_version != data.base_content_version:
        raise HTTPException(status_code=409, detail="Nội dung đã thay đổi; hãy tải lại phiên bản mới")
    proposal = DiseaseProposal(**data.model_dump(), proposer_id=actor.id)
    db.add(proposal)
    db.flush()
    record_event(db, actor_id=actor.id, action="proposal.submitted", resource_type="disease_proposal",
                 resource_id=proposal.id, details={"label_key": proposal.label_key})
    db.commit()
    db.refresh(proposal)
    return proposal


def review(db: Session, actor: User, proposal_id: int, *, approve: bool,
           note: str | None = None) -> DiseaseProposal:
    proposal = db.query(DiseaseProposal).filter(DiseaseProposal.id == proposal_id).populate_existing().with_for_update().first()
    if proposal is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề xuất")
    decision = "approved" if approve else "rejected"
    if proposal.status == decision:
        # Preserve the original review note, reviewer, time and content version.
        return proposal
    if proposal.status != "pending":
        raise HTTPException(status_code=409, detail="Đề xuất đã được xử lý theo quyết định khác")
    if approve:
        content = lock_disease(db, proposal.label_key)
        if content is None or not content.is_active or content.content_version != proposal.base_content_version:
            raise HTTPException(status_code=409, detail="Nội dung đã thay đổi hoặc bị ẩn; cần đề xuất mới")
        apply_content(content, actor.id, DiseaseInfoUpdate.model_validate({
            "disease_name": proposal.disease_name, "description": proposal.description,
            "treatment": proposal.treatment, "severity_level": proposal.severity_level,
        }))
    elif not note or not note.strip():
        raise HTTPException(status_code=422, detail="Cần lý do từ chối")
    proposal.status = decision
    proposal.reviewer_id = actor.id
    proposal.review_note = note if not approve else None
    proposal.reviewed_at = datetime.now(timezone.utc)
    record_event(db, actor_id=actor.id, action=f"proposal.{decision}", resource_type="disease_proposal",
                 resource_id=proposal.id, details={"label_key": proposal.label_key})
    db.commit()
    db.refresh(proposal)
    return proposal
