"""Tạo/xóa PostgreSQL database dành riêng cho test một cách an toàn."""

from __future__ import annotations

import os
import re

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url

from app.core.config import settings


_SAFE_TEST_DATABASE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*_test$")


def get_test_database_url(database_name: str = "plant_disease_test") -> URL:
    """Lấy PostgreSQL URL test; database bắt buộc có hậu tố ``_test``."""
    configured_url = os.getenv("TEST_DATABASE_URL", settings.DATABASE_URL)
    url = make_url(configured_url)
    if url.get_backend_name() != "postgresql":
        raise RuntimeError("Test suite chỉ hỗ trợ PostgreSQL")

    if os.getenv("TEST_DATABASE_URL") and database_name == "plant_disease_test":
        database_name = url.database or database_name
    _validate_test_database_name(database_name)
    return url.set(database=database_name)


def recreate_database(url: URL) -> None:
    """Tạo lại database test rỗng; từ chối mọi tên không kết thúc bằng _test."""
    database_name = _database_name(url)
    admin_engine = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as connection:
            connection.execute(
                text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname = :database_name AND pid <> pg_backend_pid()"
                ),
                {"database_name": database_name},
            )
            connection.exec_driver_sql(f'DROP DATABASE IF EXISTS "{database_name}"')
            connection.exec_driver_sql(f'CREATE DATABASE "{database_name}"')
    finally:
        admin_engine.dispose()


def drop_database(url: URL) -> None:
    """Xóa database test sau khi suite hoàn tất."""
    database_name = _database_name(url)
    admin_engine = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as connection:
            connection.execute(
                text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname = :database_name AND pid <> pg_backend_pid()"
                ),
                {"database_name": database_name},
            )
            connection.exec_driver_sql(f'DROP DATABASE IF EXISTS "{database_name}"')
    finally:
        admin_engine.dispose()


def _database_name(url: URL) -> str:
    database_name = url.database or ""
    _validate_test_database_name(database_name)
    return database_name


def _validate_test_database_name(database_name: str) -> None:
    if not _SAFE_TEST_DATABASE.fullmatch(database_name):
        raise RuntimeError(
            "Từ chối thao tác database test không có tên an toàn dạng *_test: "
            f"{database_name!r}"
        )
