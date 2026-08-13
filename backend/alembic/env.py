"""Module cấu hình môi trường Alembic Migration cho CSDL."""

# pylint: disable=import-error, wrong-import-position, no-member

from __future__ import annotations

from logging.config import fileConfig
import os
import sys

from alembic import context
from sqlalchemy import engine_from_config, pool

# 1. Thêm thư mục gốc dự án vào Python Path
sys.path.insert(0, os.path.abspath("."))

# Thêm type: ignore để Pylance/MyPy không báo gạch đỏ IDE
from app.core.config import settings  # type: ignore # noqa: E402
from app.db.base import Base  # type: ignore # noqa: E402
from app.models.user import User  # type: ignore # noqa: E402, F401

# 2. Lấy đối tượng Alembic Config
config = context.config

# 3. Ép kiểu str() để đảm bảo tương thích tuyệt đối với Pydantic v2
config.set_main_option("sqlalchemy.url", str(settings.DATABASE_URL))

# Cấu hình logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Gán MetaData chuẩn cho Alembic autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Chạy migration ở chế độ offline (xuất ra SQL script)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        render_as_batch=True,  # Bắt buộc cho SQLite
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Chạy migration trực tiếp kết nối với CSDL."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=True,  # Bắt buộc cho SQLite
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()