"""Dedicated admin oversight; never bypass personal Scan/Farm routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.api.deps import require_role
from app.api.query_params import TimeWindow, time_window
from app.db.session import get_db
from app.models.farm import Farm
from app.models.scan import Scan
from app.models.user import User
from app.schemas.predict import ValidationStatus
from app.schemas.stats import AdminOverview, AdminScanItem, ScanStats
from app.services import farm_service, stats_service
from app.services.audit_service import record_event
from app.services.image_storage_service import resolve_stored_image

router = APIRouter(tags=["Monitoring"])


@router.get("/stats/farm/{farm_id}", response_model=ScanStats)
def farm_stats(farm_id: int, window: TimeWindow = Depends(time_window),
               db: Session = Depends(get_db), actor: User = Depends(require_role("manager"))) -> ScanStats:
    farm_service.get_farm(db, actor, farm_id)
    return stats_service.summarize(stats_service.scan_query(db, window).filter(Scan.farm_id == farm_id))


@router.get("/stats/admin/overview", response_model=AdminOverview)
def admin_overview(window: TimeWindow = Depends(time_window), db: Session = Depends(get_db),
                   _actor: User = Depends(require_role("admin"))) -> AdminOverview:
    counts = stats_service.summarize(stats_service.scan_query(db, window))
    return AdminOverview(**counts.model_dump(), total_users=db.query(User).count(),
                         active_users=db.query(User).filter(User.status == "active").count(),
                         total_farms=db.query(Farm).count(),
                         active_farms=db.query(Farm).filter(Farm.archived_at.is_(None)).count())


@router.get("/admin/scans", response_model=list[AdminScanItem])
def admin_scans(user_id: int | None = Query(None, ge=1),
                validation_status: ValidationStatus | None = Query(None),
                is_valid_leaf: bool | None = Query(None),
                limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0),
                window: TimeWindow = Depends(time_window), db: Session = Depends(get_db),
                _actor: User = Depends(require_role("admin"))) -> list[Scan]:
    query = stats_service.scan_query(db, window)
    if user_id is not None:
        query = query.filter(Scan.user_id == user_id)
    if validation_status is not None:
        query = query.filter(Scan.validation_status == validation_status)
    if is_valid_leaf is not None:
        query = query.filter(Scan.is_valid_leaf == is_valid_leaf)
    return query.order_by(Scan.created_at.desc(), Scan.id.desc()).offset(offset).limit(limit).all()


@router.get("/stats/admin/recent-invalid", response_model=list[AdminScanItem])
def recent_invalid(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0),
                   window: TimeWindow = Depends(time_window), db: Session = Depends(get_db),
                   _actor: User = Depends(require_role("admin"))) -> list[Scan]:
    return stats_service.scan_query(db, window).filter(stats_service.rejected_condition()).order_by(
        Scan.created_at.desc(), Scan.id.desc()).offset(offset).limit(limit).all()


@router.get("/admin/scans/{scan_id}/image", response_class=FileResponse)
def admin_scan_image(scan_id: int, db: Session = Depends(get_db),
                     actor: User = Depends(require_role("admin"))) -> FileResponse:
    scan = db.get(Scan, scan_id)
    path = resolve_stored_image(scan.image_path) if scan is not None else None
    if path is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy ảnh Scan")
    record_event(db, actor_id=actor.id, action="scan.image_access_authorized", resource_type="scan",
                 resource_id=scan_id, details={})
    db.commit()  # Fail closed if the oversight audit cannot be saved.
    return FileResponse(path, media_type="image/png" if path.suffix.lower() == ".png" else "image/jpeg",
                        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})
