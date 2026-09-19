"""Offline PostgreSQL + uploads backup; restore ONLY into a new *_restore_test DB.

Use only trusted bundles produced by this tool. Stop all API workers/jobs and
wait for in-flight requests before backup: DB and files cannot share a snapshot.
No command overwrites, drops, terminates sessions, or changes the source DB.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
from typing import Any

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import URL, make_url

from app.core.config import settings


class BackupError(RuntimeError):
    pass


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def pg_command(bin_dir: Path, name: str, url: URL, arguments: list[str]) -> None:
    executable = bin_dir / (name + (".exe" if os.name == "nt" else ""))
    if not executable.is_file():
        raise BackupError(f"Missing PostgreSQL tool: {name}")
    env = {key: value for key, value in os.environ.items() if not key.startswith("PG")}
    env.update(PGHOST=url.host or "127.0.0.1", PGPORT=str(url.port or 5432),
               PGUSER=url.username or "", PGPASSWORD=url.password or "",
               PGDATABASE=url.database or "", PGCONNECT_TIMEOUT="10", PGOPTIONS="-c timezone=UTC")
    ssl_parameters = {"sslmode": "PGSSLMODE", "sslrootcert": "PGSSLROOTCERT",
                      "sslcert": "PGSSLCERT", "sslkey": "PGSSLKEY"}
    for key, value in url.query.items():
        if key not in ssl_parameters or not isinstance(value, str):
            raise BackupError("Unsupported database URL query parameter; configure libpq TLS explicitly")
        env[ssl_parameters[key]] = value
    result = subprocess.run([str(executable), *arguments], env=env, capture_output=True,
                            timeout=600, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    if result.returncode:
        # Do not echo stderr: it can contain connection details or row contents.
        raise BackupError(f"{name} failed (exit {result.returncode}); bundle is not verified")


def database_inventory(url: URL) -> dict[str, Any]:
    engine = create_engine(url, connect_args={"connect_timeout": 5, "options": "-c timezone=UTC"})
    try:
        with engine.connect() as connection:
            inspector = inspect(connection)
            tables = sorted(inspector.get_table_names(schema="public"))
            if not {"users", "scans", "disease_info", "alembic_version"} <= set(tables):
                raise BackupError("Source must be a migrated Plant Disease database")
            quote = connection.dialect.identifier_preparer.quote
            entries = {}
            for table in tables:
                keys = inspector.get_pk_constraint(table, schema="public")["constrained_columns"]
                if not keys:
                    raise BackupError("A table has no primary key; cannot verify stable row digest")
                order = ", ".join(quote(key) for key in keys)
                rows = connection.execution_options(stream_results=True).execute(text(
                    f"SELECT row_to_json(t)::text FROM public.{quote(table)} AS t ORDER BY {order}"
                ))
                count = 0
                row_digest = hashlib.sha256()
                for row in rows:
                    row_digest.update(row[0].encode("utf-8") + b"\n")
                    count += 1
                entries[table] = {"count": count, "sha256": row_digest.hexdigest()}
            revision = connection.execute(text("SELECT version_num FROM alembic_version ORDER BY version_num")).scalars().all()
            paths = connection.execute(text("SELECT image_path FROM scans ORDER BY id")).scalars().all()
            return {"tables": entries, "revisions": revision, "scan_image_paths": paths}
    finally:
        engine.dispose()


def image_inventory(root: Path) -> dict[str, str]:
    if not root.is_dir() or root.is_symlink():
        raise BackupError("Uploads directory missing or symlinked")
    root = root.resolve()
    files = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise BackupError("Symlink or escaped path in uploads")
        if path.is_dir() or path.name == ".gitkeep":
            continue
        if path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            raise BackupError("Unexpected non-image file in uploads; inspect it before backup")
        files[path.relative_to(root).as_posix()] = digest(path)
    return files


def check_scan_images(paths: list[str], files: dict[str, str]) -> None:
    for path in paths:
        prefix = "storage/uploads/"
        normalized = path.replace("\\", "/")
        if not normalized.startswith(prefix) or normalized.removeprefix(prefix) not in files:
            raise BackupError("A Scan references a missing/unsupported image path; backup is incomplete")


def backup(url: URL, uploads: Path, output: Path, bin_dir: Path, *, writers_stopped: bool) -> dict[str, Any]:
    if not writers_stopped:
        raise BackupError("Stop ALL writers and in-flight requests, then acknowledge --writers-stopped")
    if uploads.is_symlink() or output.exists() or output.is_symlink():
        raise BackupError("Uploads must not be symlinked; backup output must be a NEW path")
    uploads = uploads.resolve()
    output = output.resolve()
    if output.is_relative_to(uploads) or uploads.is_relative_to(output):
        raise BackupError("Backup directory must be separate from uploads")
    before = database_inventory(url)
    images = image_inventory(uploads)
    check_scan_images(before["scan_image_paths"], images)
    output.mkdir(parents=True, exist_ok=False)
    pg_command(bin_dir, "pg_dump", url, ["--format=custom", "--no-owner", "--no-privileges",
                                        "--file", str(output / "database.dump")])
    destination = output / "uploads"
    destination.mkdir()
    for name in images:
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(uploads / name, target)
    if (before != database_inventory(url) or images != image_inventory(uploads)
            or images != image_inventory(destination)):
        raise BackupError("Data changed during backup; bundle invalid. Stop writers and retry to a NEW directory")
    manifest = {"format_version": 1, "source_database": url.database,
                "scope": "database_and_uploads_no_model_bundles", "writers_stopped_acknowledged": True,
                "database": before, "images": images, "dump_sha256": digest(output / "database.dump")}
    # Manifest is the completion marker; it is written only after verification.
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def verify_bundle(bundle: Path) -> dict[str, Any]:
    if bundle.is_symlink() or any(path.is_symlink() for path in bundle.rglob("*")):
        raise BackupError("Symlinked backup bundle is not supported")
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("format_version") != 1 or manifest.get("scope") != "database_and_uploads_no_model_bundles":
        raise BackupError("Unsupported backup format")
    for name in manifest["images"]:
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name:
            raise BackupError("Unsafe path in manifest")
    if digest(bundle / "database.dump") != manifest["dump_sha256"]:
        raise BackupError("Database dump checksum mismatch")
    if image_inventory(bundle / "uploads") != manifest["images"]:
        raise BackupError("Image checksum mismatch")
    check_scan_images(manifest["database"]["scan_image_paths"], manifest["images"])
    return manifest


def restore(source_url: URL, bundle: Path, database: str, uploads: Path, bin_dir: Path) -> dict[str, Any]:
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,45}_restore_test", database):
        raise BackupError("Restore database must be a new lowercase name ending _restore_test (max 59 chars)")
    manifest = verify_bundle(bundle)
    if database in {source_url.database, manifest["source_database"]}:
        raise BackupError("Refusing to restore into source database")
    if uploads.is_symlink():
        raise BackupError("Restore uploads must not be a symlink")
    uploads = uploads.resolve()
    protected = [Path(settings.UPLOAD_DIR).resolve(), bundle.resolve()]
    if uploads.exists() or any(uploads.is_relative_to(p) or p.is_relative_to(uploads) for p in protected):
        raise BackupError("Restore uploads must be a NEW directory, separate from app uploads and bundle")
    target_url = source_url.set(database=database)
    admin = create_engine(source_url.set(database="postgres"), isolation_level="AUTOCOMMIT",
                          connect_args={"connect_timeout": 5})
    try:
        with admin.connect() as connection:
            if connection.execute(text("SELECT 1 FROM pg_database WHERE datname=:name"), {"name": database}).first():
                raise BackupError("Target database already exists; refusing to overwrite it")
            # The validated identifier cannot contain SQL metacharacters.
            connection.exec_driver_sql(f'CREATE DATABASE "{database}"')
    finally:
        admin.dispose()
    # On failure leave the new DB/directory for inspection. Never drop any DB.
    pg_command(bin_dir, "pg_restore", target_url, ["--dbname", database, "--no-owner", "--no-privileges",
                                                "--single-transaction", "--exit-on-error", str(bundle / "database.dump")])
    shutil.copytree(bundle / "uploads", uploads, dirs_exist_ok=False)
    actual = database_inventory(target_url)
    if actual != manifest["database"] or image_inventory(uploads) != manifest["images"]:
        raise BackupError("Restored data failed verification; do not promote this restore")
    return {"verified": True, "target_database": database, "scope": manifest["scope"],
            "revisions": actual["revisions"],
            "table_counts": {name: item["count"] for name, item in actual["tables"].items()},
            "row_digests_match": True, "images_verified": len(manifest["images"])}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pg-bin", required=True, type=Path)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("backup")
    create.add_argument("--output", type=Path, required=True)
    create.add_argument("--uploads", type=Path, default=Path(settings.UPLOAD_DIR))
    create.add_argument("--writers-stopped", action="store_true")
    recover = sub.add_parser("restore")
    recover.add_argument("--bundle", type=Path, required=True)
    recover.add_argument("--database", required=True)
    recover.add_argument("--uploads", type=Path, required=True)
    args = parser.parse_args()
    url = make_url(settings.DATABASE_URL)
    try:
        if args.command == "backup":
            result = backup(url, args.uploads, args.output, args.pg_bin, writers_stopped=args.writers_stopped)
            print("Verified offline backup created (contains sensitive data; protect access)")
        else:
            result = restore(url, args.bundle, args.database, args.uploads, args.pg_bin)
            print(json.dumps(result, ensure_ascii=False, indent=2))
    except BackupError as exc:
        raise SystemExit(str(exc)) from None
    except Exception:
        # Operational failures may carry passwords/SQL rows; do not dump traces.
        raise SystemExit("Backup/restore failed safely. Verify paths, DB/tool version and permissions; never overwrite targets.") from None


if __name__ == "__main__":
    main()
