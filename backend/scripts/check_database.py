"""Kiểm tra nhanh backend có kết nối được database đang cấu hình."""

import sys

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import engine

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def run() -> None:
    safe_url = engine.url.render_as_string(hide_password=True)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise SystemExit(f"[FAIL] Không thể kết nối database: {safe_url}") from exc
    print(f"[PASS] Database sẵn sàng: {safe_url}")


if __name__ == "__main__":
    run()
