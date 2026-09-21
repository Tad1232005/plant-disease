"""Seed Farm demo idempotent; run only after ``scripts.seed_week2`` in development."""

from __future__ import annotations

import json
from pathlib import Path

from app.core.config import BASE_DIR, settings
from app.db.session import SessionLocal
from app.models import Farm, User


SEED_FILE = BASE_DIR / "seed_data" / "demo_farms.json"


def run() -> int:
    """Create missing demo Farms without updating or deleting existing data."""
    if settings.APP_ENV == "production":
        raise RuntimeError("Demo Farm seed is disabled in production")
    rows = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise RuntimeError("demo_farms.json phải là JSON list")
    db = SessionLocal()
    created = 0
    try:
        for row in rows:
            if not isinstance(row, dict):
                raise RuntimeError("Mỗi Farm seed phải là JSON object")
            owner_name = row.get("owner_username")
            name = row.get("name")
            location = row.get("location_text")
            if not isinstance(owner_name, str) or not isinstance(name, str):
                raise RuntimeError("Farm seed cần owner_username và name là chuỗi")
            owner = db.query(User).filter(User.username == owner_name).one_or_none()
            if owner is None or owner.role != "manager":
                raise RuntimeError(f"Không có Manager seed hợp lệ: {owner_name}")
            exists = db.query(Farm.id).filter(
                Farm.owner_id == owner.id, Farm.name == name, Farm.archived_at.is_(None)
            ).first()
            if exists is None:
                db.add(Farm(owner_id=owner.id, name=name, location_text=location))
                created += 1
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    print(f"Seed Farm demo hoàn tất: +{created} farm.")
    return created


if __name__ == "__main__":
    run()
