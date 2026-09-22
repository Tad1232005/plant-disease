"""Create the FIRST Admin without demo data or ML artifacts; local operator CLI only.

No password argument/environment fallback, no account reset, no public API.
"""
from __future__ import annotations

import argparse
import getpass
import sys

from pydantic import ValidationError
from sqlalchemy import or_, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import User
from app.schemas.user import UserCreate
from app.services.audit_service import record_event


class BootstrapError(RuntimeError):
    pass


def bootstrap_admin(db: Session, data: UserCreate) -> int:
    """One transaction, serializes competing bootstrap commands on this DB."""
    try:
        db.execute(text("SELECT pg_advisory_xact_lock(72183019)"))
        if db.query(User.id).filter(User.role == "admin").first() is not None:
            raise BootstrapError("An Admin already exists; bootstrap cannot reset or add another Admin")
        condition = User.username == data.username
        if data.email is not None:
            condition = or_(condition, User.email == str(data.email))
        if db.query(User.id).filter(condition).first() is not None:
            raise BootstrapError("Username/email already in use; existing accounts are never promoted")
        user = User(username=data.username, email=str(data.email) if data.email else None,
                    full_name=data.full_name, password_hash=hash_password(data.password),
                    role="admin", status="active", token_version=0)
        db.add(user)
        db.flush()
        admin_id = user.id
        record_event(db, actor_id=admin_id, action="user.bootstrap_admin", resource_type="user",
                     resource_id=admin_id, details={"source": "local_operator_cli"})
        db.commit()
        return admin_id
    except Exception:
        db.rollback()
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", required=True)
    parser.add_argument("--email")
    parser.add_argument("--full-name")
    parser.add_argument("--confirm-create", action="store_true")
    args = parser.parse_args(argv)
    if not args.confirm_create or not sys.stdin.isatty():
        print("Use an interactive terminal and --confirm-create after verifying the target DB")
        return 1
    try:
        password = getpass.getpass("New Admin password (hidden): ")
        if password != getpass.getpass("Repeat password: "):
            raise BootstrapError("Passwords do not match")
        data = UserCreate(username=args.username, email=args.email, full_name=args.full_name, password=password)
        from app.db.session import SessionLocal
        with SessionLocal() as db:
            admin_id = bootstrap_admin(db, data)
    except ValidationError:
        print("Invalid account fields/password; follow the registration validation rules")
        return 1
    except BootstrapError as exc:
        print(str(exc))
        return 1
    except SQLAlchemyError:
        print("Bootstrap failed; verify DB connectivity, migration and permissions (no account committed)")
        return 1
    except (EOFError, KeyboardInterrupt):
        print("Bootstrap cancelled")
        return 1
    print(f"Created initial Admin id={admin_id}; no demo users or model records created")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
