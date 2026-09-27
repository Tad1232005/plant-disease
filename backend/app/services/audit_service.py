"""Append events in the caller's transaction (no implicit commit).

Tất cả hàm ở đây chỉ thêm vào session; commit do caller quyết định.
Không raise exception nếu audit fail — audit không được làm hỏng business flow.
"""

from typing import Any
from sqlalchemy.orm import Session
from app.models.audit_event import AuditEvent


def record_event(db: Session, *, actor_id: int | None, action: str,
                 resource_type: str, resource_id: int, details: dict[str, Any]) -> None:
    # Only explicitly constructed metadata from service code is accepted here.
    db.add(AuditEvent(actor_id=actor_id, action=action, resource_type=resource_type,
                      resource_id=str(resource_id), details=details))


# ── User Management ───────────────────────────────────────────────────────────

def audit_user_status_changed(db: Session, *, actor_id: int, target_id: int,
                               from_status: str, to_status: str, reason: str) -> None:
    """Ghi lại sự kiện suspend/activate tài khoản."""
    record_event(db, actor_id=actor_id, action="user.status_changed", resource_type="user",
                 resource_id=target_id,
                 details={"from": from_status, "to": to_status, "reason": reason})


def audit_user_created(db: Session, *, actor_id: int, user_id: int,
                        role: str, created_by_role: str) -> None:
    """Ghi lại sự kiện admin/manager tạo tài khoản."""
    record_event(db, actor_id=actor_id, action="user.provisioned", resource_type="user",
                 resource_id=user_id,
                 details={"role": role, "provisioned_by_role": created_by_role})


def audit_password_changed(db: Session, *, actor_id: int) -> None:
    """Ghi lại sự kiện đổi mật khẩu."""
    record_event(db, actor_id=actor_id, action="user.password_changed",
                 resource_type="user", resource_id=actor_id, details={})


# ── Disease Proposals ─────────────────────────────────────────────────────────

def audit_proposal_submitted(db: Session, *, actor_id: int, proposal_id: int,
                              label_key: str) -> None:
    record_event(db, actor_id=actor_id, action="proposal.submitted",
                 resource_type="disease_proposal", resource_id=proposal_id,
                 details={"label_key": label_key})


def audit_proposal_reviewed(db: Session, *, actor_id: int, proposal_id: int,
                             label_key: str, decision: str) -> None:
    record_event(db, actor_id=actor_id, action=f"proposal.{decision}",
                 resource_type="disease_proposal", resource_id=proposal_id,
                 details={"label_key": label_key, "decision": decision})


# ── Model Versions ────────────────────────────────────────────────────────────

def audit_model_registered(db: Session, *, actor_id: int, version_id: int,
                            version_name: str, model_type: str) -> None:
    record_event(db, actor_id=actor_id, action="model.registered",
                 resource_type="model_version", resource_id=version_id,
                 details={"version_name": version_name, "model_type": model_type})


def audit_model_activated(db: Session, *, actor_id: int, version_id: int,
                           version_name: str, model_type: str,
                           deactivated_version_id: int | None) -> None:
    record_event(db, actor_id=actor_id, action="model.activated",
                 resource_type="model_version", resource_id=version_id,
                 details={"version_name": version_name, "model_type": model_type,
                          "deactivated_version_id": deactivated_version_id})


# ── Farms ─────────────────────────────────────────────────────────────────────

def audit_farm_archived(db: Session, *, actor_id: int, farm_id: int,
                         farm_name: str) -> None:
    record_event(db, actor_id=actor_id, action="farm.archived",
                 resource_type="farm", resource_id=farm_id,
                 details={"farm_name": farm_name})
