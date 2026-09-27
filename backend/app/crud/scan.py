"""CRUD thuần cho lịch sử Scan."""

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.models.scan import Scan
from app.models.scan_model_result import ScanModelResult


def get_scans_by_user(
    db: Session,
    user_id: int,
    *,
    limit: int,
    offset: int,
    farm_id: int | None = None,
) -> list[Scan]:
    """Lấy lịch sử của đúng một user, mới nhất trước; tùy chọn lọc theo farm."""
    query = (
        db.query(Scan)
        .options(selectinload(Scan.topk_results))
        .filter(Scan.user_id == user_id)
    )
    if farm_id is not None:
        query = query.filter(Scan.farm_id == farm_id)
    return (
        query
        .order_by(Scan.created_at.desc(), Scan.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def count_scans_by_user(
    db: Session,
    user_id: int,
    *,
    farm_id: int | None = None,
) -> int:
    """Đếm tổng số scan của user, hỗ trợ pagination."""
    query = db.query(func.count(Scan.id)).filter(Scan.user_id == user_id)
    if farm_id is not None:
        query = query.filter(Scan.farm_id == farm_id)
    result = query.scalar()
    return result if result is not None else 0


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
