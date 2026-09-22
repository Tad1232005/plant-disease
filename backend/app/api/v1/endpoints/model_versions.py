"""API Admin quản lý Model Version: list, detail, register, activate."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.user import User
from app.schemas.model_version import (
    ActivateModelVersionResponse,
    ModelVersionListItem,
    ModelVersionResponse,
    RegisterModelVersionRequest,
)
from app.services import model_version_service

router = APIRouter(prefix="/admin/model-versions", tags=["Model Versions"])


@router.get("", response_model=list[ModelVersionListItem])
def list_versions(
    model_type: str | None = Query(None, min_length=1, max_length=30),
    is_active: bool | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _actor: User = Depends(require_role("admin")),
) -> list:
    """Liệt kê tất cả Model Version; lọc theo model_type và/hoặc is_active."""
    return model_version_service.list_model_versions(
        db, model_type=model_type, is_active=is_active, limit=limit, offset=offset
    )


@router.get("/{version_id}", response_model=ModelVersionResponse)
def get_version(
    version_id: int,
    db: Session = Depends(get_db),
    _actor: User = Depends(require_role("admin")),
):
    """Chi tiết một Model Version."""
    return model_version_service.get_model_version(db, version_id)


@router.post("", response_model=ModelVersionResponse, status_code=201)
def register_version(
    data: RegisterModelVersionRequest,
    db: Session = Depends(get_db),
    _actor: User = Depends(require_role("admin")),
):
    """Đăng ký Model Version mới từ manifest.json trên server.

    Version sau khi đăng ký ở trạng thái inactive.
    Gọi POST /{id}/activate để đưa vào sản xuất.
    """
    return model_version_service.register_version(db, data)


@router.post("/{version_id}/activate", response_model=ActivateModelVersionResponse)
def activate_version(
    version_id: int,
    db: Session = Depends(get_db),
    _actor: User = Depends(require_role("admin")),
):
    """Validate artifact → warm-up → activate trong một transaction.

    Version cũ cùng model_type bị deactivate tự động.
    Ba model_type khác nhau có thể active song song.
    Nếu warm-up thất bại, transaction rollback và version cũ giữ nguyên.
    """
    version, old_version, warmup_ms = model_version_service.activate_version(db, version_id)
    response_data = ModelVersionResponse.model_validate(version).model_dump()
    response_data["deactivated_version_id"] = old_version.id if old_version else None
    response_data["deactivated_version_name"] = old_version.version_name if old_version else None
    response_data["warmup_latency_ms"] = round(warmup_ms, 2) if warmup_ms else None
    return response_data
