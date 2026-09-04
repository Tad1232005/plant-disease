"""CRUD thuần cho lịch sử Scan."""

from sqlalchemy.orm import Session, selectinload

from app.models.scan import Scan
from app.models.scan_model_result import ScanModelResult


def get_scans_by_user(
    db: Session,
    user_id: int,
    *,
    limit: int,
    offset: int,
) -> list[Scan]:
    """Lấy lịch sử của đúng một user, mới nhất trước."""
    return (
        db.query(Scan)
        .filter(Scan.user_id == user_id)
        .order_by(Scan.created_at.desc(), Scan.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_scan_by_id(db: Session, scan_id: int) -> Scan | None:
    """Lấy scan và eager-load top-k."""
    return (
        db.query(Scan)
        .options(
            selectinload(Scan.topk_results),
            selectinload(Scan.model_results).selectinload(
                ScanModelResult.model_version
            ),
        )
        .filter(Scan.id == scan_id)
        .first()
    )
