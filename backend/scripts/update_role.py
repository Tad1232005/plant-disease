"""CLI cập nhật role user trên database được cấu hình trong ``.env``."""

import argparse
import sys

from app.db.session import SessionLocal
from app.models.user import User


ALLOWED_ROLES = ("user", "technician", "manager", "admin")


def main() -> None:
    """Cập nhật role và thu hồi token cũ của một user."""
    parser = argparse.ArgumentParser(description="Cập nhật role của user")
    parser.add_argument("username", help="Username cần cập nhật")
    parser.add_argument("role", choices=ALLOWED_ROLES, help="Role mới")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == args.username).one_or_none()
        if user is None:
            raise SystemExit(f"Không tìm thấy user: {args.username}")

        old_role = user.role
        user.role = args.role
        # Role là dữ liệu phân quyền: mọi JWT đã phát trước đó phải hết hiệu lực.
        user.token_version += 1
        db.commit()
        print(
            f"Đã đổi role của {user.username}: {old_role} -> {user.role}; "
            f"token_version={user.token_version}"
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
