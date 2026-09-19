"""Non-ML deployment regressions; PostgreSQL is always a separate test database."""
import json
import os
from concurrent.futures import ThreadPoolExecutor
import subprocess
import sys

import pytest
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.core.config import BASE_DIR, Settings, settings
from app.core.release import SCHEMA_REVISION
from app.core.security import verify_password
from app.models import AuditEvent, ModelVersion, User
from app.schemas.user import UserCreate
from scripts.bootstrap_admin import BootstrapError, bootstrap_admin
from scripts.preflight import database_checks, inspect_runtime
from tests.conftest import TEST_DATABASE_URL


def config(**overrides):
    values = dict(APP_ENV="test", DATABASE_URL="postgresql+psycopg://test:unique-db-credential@127.0.0.1:55439/demo_test",
                  SECRET_KEY="83a7cd7ff6a0de679433fd4411758a231c50790622c3d60901dbd6bbe060d7ae",
                  COOKIE_SECURE=False, COOKIE_SAMESITE="lax",
                  CORS_ORIGINS=["http://localhost:5173"], PUBLIC_API_ORIGIN="http://127.0.0.1:8000")
    values.update(overrides)
    return Settings(_env_file=None, **values)


def production(**overrides):
    values = dict(APP_ENV="production", COOKIE_SECURE=True,
                  CORS_ORIGINS=["https://plants.example.org"], PUBLIC_API_ORIGIN="https://api.example.org")
    values.update(overrides)
    return config(**values)


def test_production_configuration_accepts_secure_values():
    assert production().APP_ENV == "production"
    assert production(COOKIE_SAMESITE="none").COOKIE_SECURE


@pytest.mark.parametrize("overrides", [
    {"SECRET_KEY": "short"}, {"SECRET_KEY": "change-this-secret-key-in-production"},
    {"COOKIE_SECURE": False}, {"CORS_ORIGINS": ["http://localhost:5173"]},
    {"PUBLIC_API_ORIGIN": "http://api.example.org"},
    {"DATABASE_URL": "postgresql+psycopg://test:plant_dev_password@127.0.0.1/db"},
    {"DATABASE_URL": "postgresql+psycopg://test@127.0.0.1/db"},
])
def test_production_rejects_insecure_settings(overrides):
    with pytest.raises(ValidationError):
        production(**overrides)


@pytest.mark.parametrize("overrides", [
    {"COOKIE_SAMESITE": "none"}, {"CORS_ORIGINS": ["*"]},
    {"CORS_ORIGINS": ["https://site.example/path"]},
    {"CORS_ORIGINS": ["https://user:password@site.example"]},
    {"CORS_ORIGINS": ["https://site.example:99999"]},
    {"REFRESH_COOKIE_PATH": "/other"}, {"ALGORITHM": "none"},
    {"MAX_CONCURRENT_INFERENCES": 0}, {"INFERENCE_TIMEOUT_SECONDS": float("inf")},
    {"MAX_UPLOAD_BYTES": -1}, {"DB_POOL_SIZE": 0}, {"DB_MAX_OVERFLOW": -1},
    {"POSTGRES_PORT": 65536}, {"ACCESS_TOKEN_EXPIRE_MINUTES": 0},
])
def test_invalid_operational_settings_fail_fast(overrides):
    with pytest.raises(ValidationError):
        config(**overrides)


def test_validation_errors_do_not_echo_credentials():
    with pytest.raises(ValidationError) as exc:
        config(COOKIE_SAMESITE="none")
    assert "unique-db-credential" not in str(exc.value)
    assert "unique-db-credential" not in repr(config())


def test_cookie_path_can_be_the_exact_refresh_endpoint():
    assert config(REFRESH_COOKIE_PATH="/api/v1/auth/refresh").REFRESH_COOKIE_PATH.endswith("/refresh")


def test_config_only_preflight_never_connects(monkeypatch):
    from scripts import preflight
    monkeypatch.setattr(preflight, "database_checks", lambda *_: pytest.fail("Unexpected DB connection"))
    report = inspect_runtime(config(), config_only=True)
    assert report["ok"] and report["scope"] == "configuration_only"
    assert "unique-db-credential" not in json.dumps(report)
    assert "model_readiness" in report["not_checked"]


def test_preflight_detects_unreachable_db_and_missing_uploads(tmp_path):
    # Reserved port 1 on loopback: bounded failure, never hit the application DB.
    checked = config(DATABASE_URL="postgresql+psycopg://test:test@127.0.0.1:1/nonexistent_test",
                     UPLOAD_DIR=str(tmp_path / "missing"))
    report = inspect_runtime(checked)
    assert not report["ok"]
    assert {item["name"] for item in report["checks"] if item["status"] == "fail"} == {
        "database_checks", "upload_directory"}


def test_preflight_revision_and_structure_on_postgres(db_session):
    checked = config(DATABASE_URL=TEST_DATABASE_URL.render_as_string(hide_password=False))
    results = {item["name"]: item for item in database_checks(checked)}
    assert results["schema_revision"]["status"] == "fail"
    assert results["schema_structure"]["status"] == "pass"
    db_session.execute(text("CREATE TABLE alembic_version (version_num varchar(32) PRIMARY KEY)"))
    db_session.execute(text("INSERT INTO alembic_version VALUES (:revision)"), {"revision": SCHEMA_REVISION})
    db_session.commit()
    try:
        results = {item["name"]: item for item in database_checks(checked)}
        assert results["schema_revision"]["status"] == "pass"
        assert db_session.query(User).count() == 0
        db_session.execute(text("ALTER TABLE disease_info DROP COLUMN content_version"))
        db_session.commit()
        results = {item["name"]: item for item in database_checks(checked)}
        assert results["schema_structure"]["status"] == "fail"
        assert results["schema_structure"]["missing_columns"] == {"disease_info": ["content_version"]}
    finally:
        db_session.rollback()
        db_session.execute(text("DROP TABLE alembic_version"))
        db_session.commit()


def test_cookie_auth_rejects_untrusted_origin_without_setting_cookie(client, normal_user):
    payload = {"username": normal_user.username, "password": "StrongPass123!"}
    for origin in ("https://evil.example", "null", "http://localhost:5173.evil.example"):
        response = client.post("/api/v1/auth/login", json=payload, headers={"Origin": origin})
        assert response.status_code == 403
        assert "set-cookie" not in response.headers
        assert response.headers["cache-control"] == "no-store"
    assert client.post("/api/v1/auth/refresh", headers={"Sec-Fetch-Site": "cross-site"}).status_code == 403
    assert client.post("/api/v1/auth/login", json=payload, headers=[
        ("Origin", settings.CORS_ORIGINS[0]), ("Origin", "https://evil.example")]).status_code == 403


def test_trusted_browser_and_non_browser_auth_still_work(client, normal_user):
    payload = {"username": normal_user.username, "password": "StrongPass123!"}
    for headers in ({}, {"Origin": settings.CORS_ORIGINS[0]}, {"Origin": settings.PUBLIC_API_ORIGIN}):
        response = client.post("/api/v1/auth/login", json=payload, headers=headers)
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store"
        assert response.headers["x-content-type-options"] == "nosniff"
        assert client.post("/api/v1/auth/refresh", headers=headers).status_code == 200


def test_untrusted_origin_does_not_revoke_user_session(client, normal_user, user_headers):
    assert client.post("/api/v1/auth/logout", headers={**user_headers, "Origin": "https://evil.example"}).status_code == 403
    assert client.get("/api/v1/auth/me", headers=user_headers).status_code == 200


def test_bootstrap_creates_only_first_admin_with_audit(db_session):
    data = UserCreate(username="initial_admin", password="InitialStrong123!")
    admin_id = bootstrap_admin(db_session, data)
    user = db_session.get(User, admin_id)
    assert user.role == "admin" and user.status == "active" and user.created_by is None
    assert verify_password(data.password, user.password_hash)
    assert db_session.query(ModelVersion).count() == 0
    event = db_session.query(AuditEvent).one()
    assert event.action == "user.bootstrap_admin" and event.actor_id == admin_id
    assert data.password not in json.dumps(event.details)
    with pytest.raises(BootstrapError, match="already exists"):
        bootstrap_admin(db_session, UserCreate(username="second_admin", password="OtherStrong123!"))
    assert db_session.query(User).count() == 1


def test_bootstrap_never_promotes_existing_user(db_session, normal_user):
    with pytest.raises(BootstrapError, match="never promoted"):
        bootstrap_admin(db_session, UserCreate(username=normal_user.username, password="OtherStrong123!"))
    assert db_session.get(User, normal_user.id).role == "user"
    assert db_session.query(AuditEvent).count() == 0


def test_concurrent_bootstrap_creates_one_admin(db_session):
    sessions = sessionmaker(bind=db_session.get_bind())
    def attempt(index):
        with sessions() as session:
            try:
                bootstrap_admin(session, UserCreate(username=f"parallel_admin_{index}", password="OtherStrong123!"))
                return "created"
            except BootstrapError:
                return "refused"
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(attempt, range(2))) == ["created", "refused"]
    assert db_session.query(User).count() == db_session.query(AuditEvent).count() == 1


def test_bootstrap_audit_failure_rolls_back_account(db_session, monkeypatch):
    from scripts import bootstrap_admin as module
    def fail_audit(*args, **kwargs):
        raise RuntimeError("audit unavailable")
    monkeypatch.setattr(module, "record_event", fail_audit)
    with pytest.raises(RuntimeError):
        bootstrap_admin(db_session, UserCreate(username="rollback_admin", password="OtherStrong123!"))
    assert db_session.query(User).count() == 0


def test_demo_seed_refused_in_production_before_loading_models(monkeypatch):
    from scripts import seed_week2
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(seed_week2, "discover_artifacts", lambda *_: pytest.fail("Must not load model artifacts"))
    with pytest.raises(RuntimeError, match="disabled in production"):
        seed_week2.run()


def test_alembic_urlencoded_password_offline():
    env = os.environ.copy()
    env["DATABASE_URL"] = "postgresql+psycopg://test:abc%40def%25ghi@127.0.0.1:1/unused_test"
    result = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head", "--sql"],
                            cwd=BASE_DIR, env=env, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert SCHEMA_REVISION in result.stdout


def test_container_is_non_root_and_does_not_auto_migrate():
    dockerfile = (BASE_DIR / "Dockerfile").read_text()
    assert "USER 10001:10001" in dockerfile and "HEALTHCHECK" in dockerfile
    assert "--no-proxy-headers" in dockerfile
    assert "alembic upgrade" not in dockerfile
    requirements = (BASE_DIR / "requirements.txt").read_text().splitlines()
    for package in ("torch", "torchvision"):
        pinned = next(line for line in requirements if line.startswith(package + "=="))
        assert pinned + "+cpu" in dockerfile
