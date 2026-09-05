"""Smoke test chuỗi Alembic trên database rỗng, độc lập ORM create_all."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import URL

from tests.db_support import drop_database, get_test_database_url, recreate_database


BACKEND_DIR = Path(__file__).resolve().parents[1]


def _run_alembic(database_url: URL, *arguments: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["DATABASE_URL"] = database_url.render_as_string(hide_password=False)
    result = subprocess.run(
        [sys.executable, "-m", "alembic", *arguments],
        cwd=BACKEND_DIR,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"Alembic {' '.join(arguments)} thất bại:\n{result.stderr}"
        )
    return result


def test_alembic_upgrade_head_from_empty_database():
    database_url = get_test_database_url("plant_disease_migration_test")
    recreate_database(database_url)
    try:
        _run_alembic(database_url, "upgrade", "head")
        current = _run_alembic(database_url, "current")
        assert "f6a7b8c9d0e1" in current.stdout

        migration_engine = create_engine(database_url)
        tables = set(inspect(migration_engine).get_table_names())
        assert {
            "users",
            "farms",
            "farm_members",
            "disease_info",
            "model_versions",
            "scans",
            "scan_topk",
            "scan_model_results",
        } <= tables
        with migration_engine.connect() as connection:
            unvalidated_foreign_keys = connection.execute(
                text(
                    "SELECT count(*) FROM pg_constraint "
                    "WHERE contype = 'f' AND NOT convalidated"
                )
            ).scalar_one()
        migration_engine.dispose()
        assert unvalidated_foreign_keys == 0

        _run_alembic(database_url, "downgrade", "base")
    finally:
        drop_database(database_url)
