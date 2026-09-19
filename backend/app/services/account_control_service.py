"""Privileged local role maintenance; never exposed as a public role-edit API."""
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import Farm, FarmMember, User
from app.services.audit_service import record_event

ACCOUNT_CONTROL_LOCK = 560015
ALLOWED_ROLES = ("user", "technician", "manager", "admin")


class RoleChangeError(ValueError):
    pass


def lock_active_actor(db: Session, actor: User, roles: set[str]) -> User:
    """Recheck before creating dependencies that would prevent a role change."""
    expected_version = actor.token_version
    fresh = db.execute(select(User).where(User.id == actor.id).with_for_update()
                       .execution_options(populate_existing=True)).scalar_one_or_none()
    if (fresh is None or fresh.status != "active" or fresh.role not in roles
            or fresh.token_version != expected_version):
        raise HTTPException(status_code=403, detail="Quyền hoặc phiên tài khoản đã thay đổi")
    return fresh


def change_role(db: Session, *, username: str, role: str, reason: str, apply: bool = False) -> dict:
    if role not in ALLOWED_ROLES:
        raise RoleChangeError("Unsupported role")
    if not 5 <= len(reason.strip()) <= 1000:
        raise RoleChangeError("Reason must contain 5..1000 characters")
    try:
        db.execute(text("SET LOCAL lock_timeout = '5000ms'"))
        # Same lock as status transitions prevents a suspend/demotion race.
        db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": ACCOUNT_CONTROL_LOCK})
        user = db.execute(select(User).where(User.username == username).with_for_update()
                          .execution_options(populate_existing=True)).scalar_one_or_none()
        if user is None:
            raise RoleChangeError("User not found")
        previous = user.role
        report = {"user_id": user.id, "from": previous, "to": role,
                  "dry_run": not apply, "changed": False}
        if previous == role:
            db.rollback()
            return report
        if previous == "admin" and user.status == "active" and role != "admin":
            if db.query(User).filter(User.role == "admin", User.status == "active").count() <= 1:
                raise RoleChangeError("Cannot demote the last active Admin")
        if role != "manager" and db.query(Farm.id).filter(Farm.owner_id == user.id).first():
            raise RoleChangeError("User owns Farms (including archived); transfer ownership separately first")
        if previous == "manager" and role != "manager" and db.query(User.id).filter(
            User.created_by == user.id, User.role == "user"
        ).first():
            raise RoleChangeError("Manager still owns managed users; no implicit reassignment allowed")
        if role != "user":
            if db.query(FarmMember.id).filter(FarmMember.user_id == user.id).first():
                raise RoleChangeError("Farm member must keep the user role")
            creator = db.get(User, user.created_by) if user.created_by is not None else None
            if creator is not None and creator.role == "manager":
                raise RoleChangeError("Managed user must keep the user role")
        if apply:
            user.role = role
            user.token_version += 1
            record_event(db, actor_id=None, action="user.role_changed", resource_type="user",
                         resource_id=user.id, details={"from": previous, "to": role,
                                                       "reason": reason.strip(), "source": "local_operator_cli"})
            db.commit()
            report["changed"] = True
        else:
            db.rollback()
        return report
    except Exception:
        db.rollback()
        raise
