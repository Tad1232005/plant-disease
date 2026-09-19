"""Append events in the caller's transaction (no implicit commit)."""

from typing import Any
from sqlalchemy.orm import Session
from app.models.audit_event import AuditEvent


def record_event(db: Session, *, actor_id: int | None, action: str,
                 resource_type: str, resource_id: int, details: dict[str, Any]) -> None:
    # Only explicitly constructed metadata from service code is accepted here.
    db.add(AuditEvent(actor_id=actor_id, action=action, resource_type=resource_type,
                      resource_id=str(resource_id), details=details))
