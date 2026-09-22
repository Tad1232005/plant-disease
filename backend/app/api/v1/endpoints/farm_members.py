"""API Manager quản lý thành viên của Farm sở hữu."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.farm_member import FarmMember
from app.models.user import User
from app.schemas.farm_member import FarmMemberAddRequest, FarmMemberResponse
from app.services import farm_member_service

router = APIRouter(prefix="/farms", tags=["Farm Members"])


@router.post(
    "/{farm_id}/members",
    response_model=FarmMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_farm_member(
    farm_id: int,
    data: FarmMemberAddRequest,
    db: Session = Depends(get_db),
    current_manager: User = Depends(require_role("manager")),
) -> FarmMember:
    """Gán Managed User của Manager vào Farm sở hữu."""
    return farm_member_service.add_member(
        db,
        manager=current_manager,
        farm_id=farm_id,
        user_id=data.user_id,
    )


@router.get(
    "/{farm_id}/members",
    response_model=list[FarmMemberResponse],
)
def list_farm_members(
    farm_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_manager: User = Depends(require_role("manager")),
) -> list[FarmMember]:
    """Liệt kê thành viên Farm sở hữu."""
    return farm_member_service.list_members(
        db,
        manager=current_manager,
        farm_id=farm_id,
        limit=limit, offset=offset,
    )


@router.delete(
    "/{farm_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_farm_member(
    farm_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_manager: User = Depends(require_role("manager")),
) -> None:
    """Gỡ User khỏi Farm nhưng giữ nguyên tài khoản."""
    farm_member_service.remove_member(
        db,
        manager=current_manager,
        farm_id=farm_id,
        user_id=user_id,
    )
