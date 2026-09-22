"""SQL aggregates count scans, never per-model rows. No inference or model access."""
from sqlalchemy import and_, func
from sqlalchemy.orm import Query, Session
from app.api.query_params import TimeWindow
from app.models.scan import Scan
from app.schemas.stats import DiseaseCount, ScanStats


def scan_query(db: Session, window: TimeWindow) -> Query[Scan]:
    query = db.query(Scan)
    # Existing scan timestamps are stored as UTC without timezone. Do not cast
    # the DB column to timestamptz using an environment-dependent server zone.
    if window.start is not None:
        query = query.filter(Scan.created_at >= window.start.replace(tzinfo=None))
    if window.end is not None:
        query = query.filter(Scan.created_at < window.end.replace(tzinfo=None))
    return query


def accepted_condition():
    return and_(Scan.inference_mode != "legacy", Scan.validation_status == "accepted", Scan.is_valid_leaf.is_(True))


def rejected_condition():
    return and_(Scan.inference_mode != "legacy", ~accepted_condition())


def summarize(query: Query[Scan]) -> ScanStats:
    total, accepted, legacy = query.with_entities(
        func.count(Scan.id), func.count(Scan.id).filter(accepted_condition()),
        func.count(Scan.id).filter(Scan.inference_mode == "legacy"),
    ).one()
    rejected = total - accepted - legacy
    known = accepted + rejected
    diseases = query.filter(accepted_condition(), Scan.predicted_label.is_not(None)).with_entities(
        Scan.predicted_label, func.count(Scan.id).label("count")
    ).group_by(Scan.predicted_label).order_by(func.count(Scan.id).desc(), Scan.predicted_label).all()
    return ScanStats(total_scans=total, accepted_scans=accepted, rejected_scans=rejected,
                     legacy_scans=legacy, rejection_rate=rejected / known if known else None,
                     disease_counts=[DiseaseCount(label_key=label, count=count) for label, count in diseases])
