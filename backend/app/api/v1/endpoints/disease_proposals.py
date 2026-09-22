from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.api.deps import require_role
from app.api.query_params import TimeWindow, time_window
from app.db.session import get_db
from app.models.user import User
from app.models.disease_proposal import DiseaseProposal
from app.schemas.disease_proposal import ProposalCreate, ProposalResponse, ProposalStatus, RejectProposalRequest
from app.services import proposal_service

router = APIRouter(tags=["Disease Proposals"])


@router.post("/disease-proposals", response_model=ProposalResponse, status_code=201)
def submit_proposal(data: ProposalCreate, db: Session = Depends(get_db),
                    actor: User = Depends(require_role("technician"))) -> DiseaseProposal:
    return proposal_service.submit(db, actor, data)


@router.get("/disease-proposals/mine", response_model=list[ProposalResponse])
def my_proposals(status: ProposalStatus | None = Query(None),
                 limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0),
                 db: Session = Depends(get_db),
                 actor: User = Depends(require_role("technician"))) -> list[DiseaseProposal]:
    query = db.query(DiseaseProposal).filter(DiseaseProposal.proposer_id == actor.id)
    if status is not None:
        query = query.filter(DiseaseProposal.status == status)
    return query.order_by(DiseaseProposal.created_at.desc(), DiseaseProposal.id.desc()).offset(offset).limit(limit).all()


@router.get("/admin/disease-proposals", response_model=list[ProposalResponse])
def admin_proposals(status: ProposalStatus | None = Query(None),
                    label_key: str | None = Query(None, min_length=1, max_length=50),
                    proposer_id: int | None = Query(None, ge=1),
                    limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0),
                    window: TimeWindow = Depends(time_window), db: Session = Depends(get_db),
                    _actor: User = Depends(require_role("admin"))) -> list[DiseaseProposal]:
    query = db.query(DiseaseProposal)
    if status is not None:
        query = query.filter(DiseaseProposal.status == status)
    if label_key is not None:
        query = query.filter(DiseaseProposal.label_key == label_key)
    if proposer_id is not None:
        query = query.filter(DiseaseProposal.proposer_id == proposer_id)
    if window.start is not None:
        query = query.filter(DiseaseProposal.created_at >= window.start)
    if window.end is not None:
        query = query.filter(DiseaseProposal.created_at < window.end)
    return query.order_by(DiseaseProposal.created_at.desc(), DiseaseProposal.id.desc()).offset(offset).limit(limit).all()


@router.put("/admin/disease-proposals/{proposal_id}/approve", response_model=ProposalResponse)
def approve_proposal(proposal_id: int, db: Session = Depends(get_db),
                     actor: User = Depends(require_role("admin"))) -> DiseaseProposal:
    return proposal_service.review(db, actor, proposal_id, approve=True)


@router.put("/admin/disease-proposals/{proposal_id}/reject", response_model=ProposalResponse)
def reject_proposal(proposal_id: int, data: RejectProposalRequest,
                    db: Session = Depends(get_db),
                    actor: User = Depends(require_role("admin"))) -> DiseaseProposal:
    return proposal_service.review(db, actor, proposal_id, approve=False, note=data.review_note)
