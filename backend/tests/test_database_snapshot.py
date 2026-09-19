"""DB-only fallback is explicit and never claims missing images were recovered."""
import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from scripts import database_snapshot as snapshots
from scripts.backup_restore import BackupError, database_inventory
from tests.db_support import drop_database, get_test_database_url, recreate_database
from tests.test_migrations import _run_alembic


def test_snapshot_requires_explicit_scope_and_new_output(tmp_path):
    source = get_test_database_url()
    with pytest.raises(BackupError, match="acknowledgement"):
        snapshots.snapshot(source, tmp_path, tmp_path, acknowledge_no_images=False)
    with pytest.raises(BackupError, match="NEW path"):
        snapshots.snapshot(source, tmp_path, tmp_path, acknowledge_no_images=True)


def test_snapshot_rejects_invalid_restore_name(tmp_path):
    with pytest.raises(BackupError, match="Target"):
        snapshots.restore_snapshot(get_test_database_url(), tmp_path, "plant_disease", tmp_path)


def test_db_only_snapshot_restores_rows_even_when_images_missing(tmp_path):
    if not os.getenv("PG_BIN"):
        pytest.skip("PG_BIN required for real snapshot/restore")
    pg_bin = Path(os.environ["PG_BIN"])
    source = get_test_database_url("plant_snapshot_source_test")
    target = source.set(database="plant_snapshot_restore_test")
    recreate_database(source)
    drop_database(target)
    try:
        _run_alembic(source, "upgrade", "head")
        engine = create_engine(source)
        with engine.begin() as c:
            c.execute(text("INSERT INTO users(username,password_hash,role) VALUES ('snapshot_user','synthetic','user')"))
            c.execute(text("INSERT INTO scans(user_id,image_path,is_valid_leaf) VALUES (1,'storage/uploads/missing.jpg',true)"))
        engine.dispose()
        before = database_inventory(source)
        bundle = tmp_path / "snapshot"
        manifest = snapshots.snapshot(source, bundle, pg_bin, acknowledge_no_images=True)
        assert manifest["scope"] == "database_only_no_images_no_models"
        result = snapshots.restore_snapshot(source, bundle, target.database, pg_bin)
        assert result["verified"] and not result["images_recovered"]
        assert database_inventory(source) == database_inventory(target) == before
        with pytest.raises(BackupError, match="exists"):
            snapshots.restore_snapshot(source, bundle, target.database, pg_bin)
        (bundle / "database.dump").write_bytes(b"damaged")
        with pytest.raises(BackupError, match="checksum"):
            snapshots.restore_snapshot(source, bundle, "plant_snapshot_other_restore_test", pg_bin)
    finally:
        drop_database(target)
        drop_database(source)
