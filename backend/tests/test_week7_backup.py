"""Destructive operations here are limited to dedicated *_test databases."""
import json
import os
from pathlib import Path

from PIL import Image
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.core.config import BASE_DIR, settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.main import app
from scripts import backup_restore as br
from tests.db_support import get_test_database_url, recreate_database, drop_database
from tests.test_migrations import _run_alembic


@pytest.fixture
def pg_bin():
    value = os.getenv("PG_BIN")
    if not value:
        pytest.skip("Set PG_BIN to the PostgreSQL client-tools directory for a real restore drill")
    return Path(value)


def test_real_backup_restore_and_private_image(client, tmp_path, monkeypatch, pg_bin):
    source = get_test_database_url("plant_week7_backup_test")
    target = source.set(database="plant_week7_restore_test")
    recreate_database(source)
    # Test fixture explicitly owns these names; production CLI never drops DBs.
    drop_database(target)
    original_override = app.dependency_overrides[get_db]
    restored_engine = None
    try:
        _run_alembic(source, "upgrade", "head")
        engine = create_engine(source)
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO users(username,password_hash,role) VALUES ('backup_owner','test-only-hash','user')"))
            connection.execute(text("INSERT INTO disease_info(label_key,disease_name,severity_level) VALUES ('test_label','Before backup','low')"))
            connection.execute(text("INSERT INTO scans(user_id,image_path,is_valid_leaf) VALUES (1,'storage/uploads/fixture.png',true)"))
        engine.dispose()
        uploads = tmp_path / "original-uploads"
        uploads.mkdir()
        Image.new("RGB", (32, 32), color="green").save(uploads / "fixture.png")
        bundle = tmp_path / "backup"
        manifest = br.backup(source, uploads, bundle, pg_bin, writers_stopped=True)
        assert manifest["database"]["tables"]["scans"]["count"] == 1
        assert br.verify_bundle(bundle) == manifest
        restored_uploads = tmp_path / "restored-uploads"
        result = br.restore(source, bundle, target.database, restored_uploads, pg_bin)
        assert result["verified"] and result["row_digests_match"]
        assert result["images_verified"] == 1
        assert br.database_inventory(source) == manifest["database"]
        with pytest.raises(br.BackupError, match="already exists"):
            br.restore(source, bundle, target.database, tmp_path / "another-restore", pg_bin)
        restored_engine = create_engine(target)

        def restored_db():
            with Session(restored_engine) as db:
                yield db
        app.dependency_overrides[get_db] = restored_db
        monkeypatch.setattr(settings, "UPLOAD_DIR", str(restored_uploads))
        monkeypatch.setattr(settings, "DATABASE_URL", target.render_as_string(hide_password=False))
        headers = {"Authorization": "Bearer " + create_access_token(1, role="user")}
        image = client.get("/api/v1/scans/1/image", headers=headers)
        assert image.status_code == 200
        assert image.content == (uploads / "fixture.png").read_bytes()
        assert client.get("/health/ready").status_code == 200
        created = client.post("/api/v1/auth/register", json={"username": "after_restore", "password": "StrongPass123!"})
        assert created.status_code == 201 and created.json()["id"] > 1
        result.update(restored_image_http_status=200, sequence_insert_verified=True,
                      dataset="synthetic isolated test fixture", source_unchanged=True,
                      model_bundle_verification="deferred")
        if os.getenv("WEEK7_RESTORE_REPORT"):
            report = BASE_DIR / "docs" / "week7" / "restore-verification.json"
            with report.open("x", encoding="utf-8") as output:
                json.dump(result, output, indent=2)
        # Tamper tests run before any restore creation.
        (bundle / "uploads" / "fixture.png").write_bytes(b"tampered")
        with pytest.raises(br.BackupError, match="checksum"):
            br.verify_bundle(bundle)
    finally:
        app.dependency_overrides[get_db] = original_override
        if restored_engine is not None:
            restored_engine.dispose()
        drop_database(target)
        drop_database(source)


def test_backup_requires_stopped_writers(tmp_path):
    with pytest.raises(br.BackupError, match="writers"):
        br.backup(get_test_database_url(), tmp_path, tmp_path / "backup", tmp_path, writers_stopped=False)


@pytest.mark.parametrize("name", ["plant_disease", "postgres", "plant_test", "x;drop_restore_test", "../x_restore_test"])
def test_restore_rejects_unsafe_target_before_reading_bundle(tmp_path, name):
    with pytest.raises(br.BackupError, match="Restore database"):
        br.restore(get_test_database_url(), tmp_path / "nonexistent", name, tmp_path / "restored", tmp_path)


def test_missing_scan_image_rejected():
    with pytest.raises(br.BackupError):
        br.check_scan_images(["storage/uploads/missing.png"], {})
    with pytest.raises(br.BackupError):
        br.check_scan_images(["/etc/passwd"], {})


def test_image_inventory_rejects_non_image(tmp_path):
    (tmp_path / "secret.env").write_text("not an image")
    with pytest.raises(br.BackupError, match="non-image"):
        br.image_inventory(tmp_path)


def test_dump_tampering_rejected(tmp_path):
    (tmp_path / "uploads").mkdir()
    (tmp_path / "database.dump").write_bytes(b"tampered")
    (tmp_path / "manifest.json").write_text(json.dumps({
        "format_version": 1, "scope": "database_and_uploads_no_model_bundles",
        "images": {}, "dump_sha256": "0" * 64,
    }))
    with pytest.raises(br.BackupError, match="dump checksum"):
        br.verify_bundle(tmp_path)


def test_manifest_traversal_rejected(tmp_path):
    (tmp_path / "manifest.json").write_text(json.dumps({
        "format_version": 1, "scope": "database_and_uploads_no_model_bundles",
        "images": {"../outside.png": "0" * 64},
    }))
    with pytest.raises(br.BackupError, match="Unsafe path"):
        br.verify_bundle(tmp_path)
