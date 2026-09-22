from pydantic import BaseModel
from app.schemas.scan import ScanHistoryItem


class AdminScanItem(ScanHistoryItem):
    user_id: int
    rejection_reason: str | None


class DiseaseCount(BaseModel):
    label_key: str
    count: int


class ScanStats(BaseModel):
    total_scans: int
    accepted_scans: int
    rejected_scans: int
    legacy_scans: int
    rejection_rate: float | None
    disease_counts: list[DiseaseCount]


class AdminOverview(ScanStats):
    total_users: int
    active_users: int
    total_farms: int
    active_farms: int
