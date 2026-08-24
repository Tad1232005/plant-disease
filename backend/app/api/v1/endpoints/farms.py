"""API endpoint quản lý Farm."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.farm import FarmCreate, FarmUpdate, FarmResponse
from app.services import farm_service
from app.api.deps import require_role
from app.models.user import User

router = APIRouter(prefix="/farms", tags=["Farms"])


@router.post(
    "",
    response_model=FarmResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_farm(
    farm_in: FarmCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("manager", "admin")),
):
    """Tạo farm mới."""
    return farm_service.create_farm(db, current_user, farm_in)


@router.get("", response_model=list[FarmResponse])
def list_farms(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("manager", "admin")),
):
    """Lấy danh sách farm của user hiện tại."""
    return farm_service.list_farms(db, current_user)


@router.get("/{farm_id}", response_model=FarmResponse)
def get_farm(
    farm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("manager", "admin")),
):
    """Lấy chi tiết farm; Manager chỉ xem farm mình sở hữu."""
    return farm_service.get_farm(db, current_user, farm_id)


@router.put("/{farm_id}", response_model=FarmResponse)
def update_farm(
    farm_id: int,
    farm_in: FarmUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("manager", "admin")),
):
    """Cập nhật thông tin farm."""
    return farm_service.update_farm(db, current_user, farm_id, farm_in)


@router.delete("/{farm_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_farm(
    farm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("manager", "admin")),
):
    """Xóa farm."""
    farm_service.delete_farm(db, current_user, farm_id)
