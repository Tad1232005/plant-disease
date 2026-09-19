"""Explicit DB-only backup/restore drill. Does NOT back up or recover images/models.

For approved maintenance when a full DB+uploads backup is impossible. Never
overwrite a bundle/DB, never drop a DB, never silently fall back from full backup.
"""
import argparse
import json
from pathlib import Path
import re

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url

from app.core.config import settings
from scripts.backup_restore import BackupError, database_inventory, digest, pg_command


def snapshot(url: URL, output: Path, bin_dir: Path, *, acknowledge_no_images: bool) -> dict:
    if not acknowledge_no_images:
        raise BackupError("Explicit acknowledgement required: database only, images/models NOT included")
    if output.exists() or output.is_symlink():
        raise BackupError("Output must be a NEW path")
    # pg_dump takes its own consistent database snapshot. Compare all row digests
    # before/after to refuse a snapshot that diverges from the maintenance baseline.
    before = database_inventory(url)
    output.mkdir(parents=True, exist_ok=False)
    pg_command(bin_dir, "pg_dump", url, ["--format=custom", "--no-owner", "--no-privileges",
                                        "--file", str(output / "database.dump")])
    if database_inventory(url) != before:
        raise BackupError("Database changed during snapshot; stop writers and retry to a NEW path")
    manifest = {"format_version": 1, "scope": "database_only_no_images_no_models",
                "source_database": url.database, "database": before,
                "dump_sha256": digest(output / "database.dump")}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def restore_snapshot(url: URL, bundle: Path, database: str, bin_dir: Path) -> dict:
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,45}_restore_test", database):
        raise BackupError("Target must be a new lowercase *_restore_test database")
    if bundle.is_symlink() or any(p.is_symlink() for p in bundle.rglob("*")):
        raise BackupError("Symlinked bundle is not supported")
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("format_version") != 1 or manifest.get("scope") != "database_only_no_images_no_models":
        raise BackupError("This is not a DB-only snapshot")
    if database in {url.database, manifest["source_database"]}:
        raise BackupError("Cannot restore into source database")
    if digest(bundle / "database.dump") != manifest["dump_sha256"]:
        raise BackupError("Database dump checksum mismatch")
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT",
                          connect_args={"connect_timeout": 5})
    try:
        with admin.connect() as c:
            if c.execute(text("SELECT 1 FROM pg_database WHERE datname=:db"), {"db": database}).first():
                raise BackupError("Target already exists; refusing overwrite")
            c.exec_driver_sql(f'CREATE DATABASE "{database}"')
    finally:
        admin.dispose()
    target = url.set(database=database)
    pg_command(bin_dir, "pg_restore", target, ["--dbname", database, "--no-owner", "--no-privileges",
                                              "--single-transaction", "--exit-on-error", str(bundle / "database.dump")])
    restored = database_inventory(target)
    if restored != manifest["database"]:
        raise BackupError("Restored row counts/digests/revision do not match; do not use this restore")
    return {"verified": True, "scope": manifest["scope"], "target_database": database,
            "table_counts": {k: v["count"] for k, v in restored["tables"].items()},
            "row_digests_match": True, "images_recovered": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pg-bin", type=Path, required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    save = sub.add_parser("snapshot")
    save.add_argument("--output", type=Path, required=True)
    save.add_argument("--acknowledge-no-images", action="store_true")
    recover = sub.add_parser("restore")
    recover.add_argument("--bundle", type=Path, required=True)
    recover.add_argument("--database", required=True)
    args = parser.parse_args()
    try:
        url = make_url(settings.DATABASE_URL)
        if args.command == "snapshot":
            snapshot(url, args.output, args.pg_bin, acknowledge_no_images=args.acknowledge_no_images)
            print("DB-only snapshot created. Images/models NOT included. Protect this sensitive backup.")
        else:
            print(json.dumps(restore_snapshot(url, args.bundle, args.database, args.pg_bin), indent=2))
    except BackupError as exc:
        print(str(exc))
        return 1
    except Exception:
        print("Snapshot/restore failed; partial target retained for inspection, source not modified")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
