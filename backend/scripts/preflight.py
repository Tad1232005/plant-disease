"""Read-only deployment checks. Never migrates, seeds, or prints credentials."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, TYPE_CHECKING

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool

if TYPE_CHECKING:
    from app.core.config import Settings


def database_checks(config: Settings) -> list[dict[str, Any]]:
    from app.core.release import SCHEMA_REVISION
    from app.db.base import Base
    import app.models  # noqa: F401 -- populate metadata; no model weights loaded

    checks: list[dict[str, Any]] = []
    engine = create_engine(config.DATABASE_URL, poolclass=NullPool, connect_args={
        "connect_timeout": 3, "options": "-c statement_timeout=3000 -c timezone=UTC"})
    try:
        with engine.connect() as connection:
            connection.execute(text("SET TRANSACTION READ ONLY"))
            connection.execute(text("SELECT 1"))
            checks.append({"name": "database_connection", "status": "pass"})
            inspector = inspect(connection)
            tables = set(inspector.get_table_names(schema="public"))
            revisions = []
            if "alembic_version" in tables:
                revisions = list(connection.execute(text(
                    "SELECT version_num FROM public.alembic_version ORDER BY version_num"
                )).scalars())
            checks.append({"name": "schema_revision", "status": "pass" if revisions == [SCHEMA_REVISION] else "fail",
                           "expected": SCHEMA_REVISION, "actual": revisions})
            missing_tables = sorted(set(Base.metadata.tables) - tables)
            missing_columns = {}
            for name, table in Base.metadata.tables.items():
                if name in tables:
                    actual = {column["name"] for column in inspector.get_columns(name, schema="public")}
                    missing = sorted({column.name for column in table.columns} - actual)
                    if missing:
                        missing_columns[name] = missing
            checks.append({"name": "schema_structure",
                           "status": "fail" if missing_tables or missing_columns else "pass",
                           "missing_tables": missing_tables, "missing_columns": missing_columns})
            privileged = connection.execute(text(
                "SELECT rolsuper OR rolcreatedb OR rolcreaterole OR rolbypassrls "
                "FROM pg_roles WHERE rolname = current_user"
            )).scalar_one()
            checks.append({"name": "database_role_privileges",
                           "status": ("fail" if config.APP_ENV == "production" else "warning") if privileged else "pass",
                           "message": "Runtime DB role must not be superuser/CREATEDB/CREATEROLE/BYPASSRLS"})
    except SQLAlchemyError:
        # SQL/driver exception text can contain passwords, hostnames or row data.
        checks.append({"name": "database_checks", "status": "fail",
                       "message": "Cannot complete DB checks; verify connectivity, permissions and schema"})
    finally:
        engine.dispose()
    return checks


def inspect_runtime(config: Settings, *, config_only: bool = False) -> dict[str, Any]:
    from app.core.release import API_VERSION
    checks: list[dict[str, Any]] = [{"name": "configuration", "status": "pass"}]
    if not config_only:
        checks.extend(database_checks(config))
        uploads = Path(config.UPLOAD_DIR)
        accessible = uploads.is_dir() and os.access(uploads, os.R_OK | os.W_OK | os.X_OK)
        checks.append({"name": "upload_directory", "status": "pass" if accessible else "fail",
                       "message": "Directory must exist and be accessible; read-only preflight does not prove file writes"})
    if config.APP_ENV != "production":
        checks.append({"name": "deployment_mode", "status": "warning",
                       "message": "Not production mode; production security rules have not been applied"})
    return {"api_version": API_VERSION, "scope": "configuration_only" if config_only else "non_ml_runtime",
            "ok": not any(item["status"] == "fail" for item in checks), "checks": checks,
            "not_checked": ["model_readiness", "real_inference", "external_tls", "browser_integration",
                            "full_schema_type_index_constraint_drift", "backup_recovery"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-only", action="store_true", help="Validate settings without DB/filesystem access")
    args = parser.parse_args(argv)
    try:
        from app.core.config import settings
        report = inspect_runtime(settings, config_only=args.config_only)
    except (ValueError, SQLAlchemyError):
        report = {"ok": False, "checks": [{"name": "configuration", "status": "fail",
                                           "message": "Invalid settings; check the environment configuration"}]}
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
