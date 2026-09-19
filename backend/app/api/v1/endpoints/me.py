"""Farm choices for the authenticated account, without granting Farm CRUD."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.farm import Farm
from app.models.farm_member import FarmMember
from app.models.user import User
from app.schemas.farm import FarmResponse

router = APIRouter(prefix="/me", tags=["My account"])


@router.get("/farms", response_model=list[FarmResponse])
def my_farms(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Farm]:
    query = db.query(Farm).filter(Farm.archived_at.is_(None))
    if current_user.role == "manager":
        query = query.filter(Farm.owner_id == current_user.id)
    elif current_user.role == "user" and current_user.created_by is not None:
        query = query.join(FarmMember, FarmMember.farm_id == Farm.id).filter(
            FarmMember.user_id == current_user.id,
            Farm.owner_id == current_user.created_by,
        )
    else:
        return []
    return query.order_by(Farm.created_at.desc(), Farm.id.desc()).offset(offset).limit(limit).all()
