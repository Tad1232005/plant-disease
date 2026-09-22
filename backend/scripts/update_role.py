"""Privileged role maintenance. Defaults to dry-run; requires a reason and --apply."""

import argparse
import json
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import SessionLocal
from app.services.account_control_service import ALLOWED_ROLES, RoleChangeError, change_role


def main(argv: list[str] | None = None) -> int:
    """Cập nhật role và thu hồi token cũ của một user."""
    parser = argparse.ArgumentParser(description="Cập nhật role của user")
    parser.add_argument("username", help="Username cần cập nhật")
    parser.add_argument("role", choices=ALLOWED_ROLES, help="Role mới")
    parser.add_argument("--reason", required=True, help="Operational reason, 5..1000 characters")
    parser.add_argument("--apply", action="store_true", help="Commit; default validates/previews only")
    args = parser.parse_args(argv)

    try:
        with SessionLocal() as db:
            result = change_role(db, username=args.username, role=args.role, reason=args.reason, apply=args.apply)
    except RoleChangeError as exc:
        print(str(exc))
        return 1
    except SQLAlchemyError:
        print("Role change failed; transaction rolled back. Verify DB schema/permissions/connectivity")
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
