"""Smoke test chuỗi Alembic trên database rỗng, độc lập ORM create_all."""

from __future__ import annotations

import os
from pathlib import Path
import sqlite3
import subprocess
import sys


BACKEND_DIR = Path(__file__).resolve().parents[1]


def _run_alembic(database_url: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["DATABASE_URL"] = database_url
    return subprocess.run(
        [sys.executable, "-m", "alembic", *arguments],
        cwd=BACKEND_DIR,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )


def test_alembic_upgrade_head_from_empty_database(tmp_path):
    database_path = tmp_path / "migration-smoke.db"
    database_url = f"sqlite:///{database_path.resolve().as_posix()}"

    _run_alembic(database_url, "upgrade", "head")
    current = _run_alembic(database_url, "current")
    assert "f6a7b8c9d0e1" in current.stdout

    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
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
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []

    _run_alembic(database_url, "downgrade", "base")
