"""API lịch sử Scan chỉ theo quyền sở hữu của user hiện tại."""

from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.scan import Scan
from app.models.user import User
from app.schemas.scan import ScanDetailResponse, ScanHistoryItem
from app.services import scan_service

router = APIRouter(prefix="/scans", tags=["Scans"])


@router.get("/history", response_model=list[ScanHistoryItem])
def get_scan_history(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Scan]:
    """Lấy lịch sử scan của chính tài khoản đang đăng nhập."""
    return scan_service.list_history(
        db,
        current_user,
        limit=limit,
        offset=offset,
    )


@router.get("/{scan_id}", response_model=ScanDetailResponse)
def get_scan(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Lấy chi tiết scan nếu là chủ sở hữu."""
    return scan_service.get_scan_detail(db, current_user, scan_id)


@router.delete("/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scan(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Xóa scan nếu là chủ sở hữu."""
    scan_service.delete_scan(db, current_user, scan_id)
