"""Shared auth quotas, safe local role transitions, and privacy-preserving access logs."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json

from fastapi import HTTPException
import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.models import AuditEvent, AuthRateLimit, Farm, FarmMember, User
from app.schemas.farm import FarmCreate
from app.schemas.user import ManagerCreateUserRequest
from app.services import account_control_service as accounts
from app.services.auth_rate_limit_service import consume, subject_key
from app.services.farm_service import create_farm
from app.services.user_admin_service import create_user_by


def test_rate_limit_blocks_password_checks_and_survives_new_sessions(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "AUTH_LOGIN_RATE_LIMIT", 2)
    credentials = {"username": "missing", "password": "NotARealPassword123!"}
    for _ in range(2):
        assert client.post("/api/v1/auth/login", json=credentials).status_code == 401
    blocked = client.post("/api/v1/auth/login", json=credentials)
    assert blocked.status_code == 429 and 1 <= int(blocked.headers["retry-after"]) <= 300
    assert blocked.headers["cache-control"] == "no-store"
    assert len(blocked.headers["x-request-id"]) == 32
    counter = db_session.query(AuthRateLimit).one()
    assert "missing" not in counter.bucket_key and len(counter.bucket_key) == 64
    with Session(db_session.get_bind()) as other_worker:
        assert not consume(other_worker, key=counter.bucket_key, limit=2, window_seconds=300).allowed


@pytest.mark.parametrize("path,field,payload", [
    ("register", "AUTH_REGISTER_RATE_LIMIT", {"username": "weak", "password": "short"}),
    ("refresh", "AUTH_REFRESH_RATE_LIMIT", {}),
    ("change-password", "AUTH_PASSWORD_RATE_LIMIT", {"current_password": "abc", "new_password": "NewStrong123!"}),
])
def test_each_auth_quota_applies_independently(client, monkeypatch, path, field, payload):
    monkeypatch.setattr(settings, field, 1)
    assert client.post(f"/api/v1/auth/{path}", json=payload).status_code in {401, 422}
    assert client.post(f"/api/v1/auth/{path}", json=payload).status_code == 429
    assert client.post("/api/v1/auth/logout").status_code == 401


def test_proxy_header_spoof_does_not_reset_quota(client, monkeypatch):
    monkeypatch.setattr(settings, "AUTH_REFRESH_RATE_LIMIT", 1)
    assert client.post("/api/v1/auth/refresh", headers={"X-Forwarded-For": "192.0.2.1"}).status_code == 401
    assert client.post("/api/v1/auth/refresh", headers={"X-Forwarded-For": "192.0.2.2"}).status_code == 429


def test_untrusted_origin_does_not_consume_auth_quota(client, db_session):
    assert client.post("/api/v1/auth/refresh", headers={"Origin": "https://bad.example"}).status_code == 403
    assert db_session.query(AuthRateLimit).count() == 0


def test_rate_limit_recovers_after_expiry(db_session):
    key = "b" * 64
    assert consume(db_session, key=key, limit=1, window_seconds=300).allowed
    assert not consume(db_session, key=key, limit=1, window_seconds=300).allowed
    db_session.execute(text("UPDATE auth_rate_limits SET expires_at=now()-interval '1 second'"))
    db_session.commit()
    assert consume(db_session, key=key, limit=1, window_seconds=300).allowed
    assert db_session.get(AuthRateLimit, key).attempts == 1


def test_rate_limit_concurrent_requests_share_atomic_budget(db_session):
    sessions = sessionmaker(bind=db_session.get_bind())
    def request(_):
        with sessions() as db:
            return consume(db, key="c" * 64, limit=3, window_seconds=300).allowed
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(request, range(8))) == 3
    assert db_session.get(AuthRateLimit, "c" * 64).attempts == 4


def test_rate_limit_cleanup_is_bounded_and_keeps_live_counters(db_session):
    for i in range(105):
        db_session.add(AuthRateLimit(bucket_key=f"{i:064x}", attempts=1,
                                    expires_at=datetime.now(timezone.utc) - timedelta(days=2)))
    db_session.commit()
    consume(db_session, key="d" * 64, limit=1, window_seconds=300)
    assert db_session.query(AuthRateLimit).count() == 6
    assert db_session.get(AuthRateLimit, "d" * 64).attempts == 1


def test_limiter_db_failure_is_503_not_bypass_or_secret_leak(client, monkeypatch):
    from app.api import auth_rate_limit
    def unavailable(*args, **kwargs):
        raise SQLAlchemyError("sensitive-connection-detail")
    monkeypatch.setattr(auth_rate_limit, "consume", unavailable)
    response = client.post("/api/v1/auth/refresh")
    assert response.status_code == 503 and response.headers["retry-after"] == "5"
    assert "sensitive-connection-detail" not in response.text


def test_subject_keys_hide_ip_and_group_ipv6_subnet():
    assert subject_key("::ffff:192.0.2.1", "login", "key") == subject_key("192.0.2.1", "login", "key")
    assert subject_key("192.0.2.1", "login", "key") != subject_key("192.0.2.2", "login", "key")
    assert subject_key("192.0.2.1", "login", "key") != subject_key("192.0.2.1", "refresh", "key")
    assert subject_key("2001:db8::1", "login", "key") == subject_key("2001:db8::2", "login", "key")


def change(db, user, role, *, apply=True):
    return accounts.change_role(db, username=user.username, role=role, reason="Approved maintenance", apply=apply)


def test_role_change_preview_is_read_only_and_apply_revokes_tokens(client, db_session, normal_user, user_headers):
    preview = change(db_session, normal_user, "technician", apply=False)
    assert preview["dry_run"] and not preview["changed"]
    assert db_session.get(User, normal_user.id).role == "user"
    assert db_session.query(AuditEvent).count() == 0
    assert change(db_session, normal_user, "technician")["changed"]
    assert normal_user.token_version == 1 and normal_user.role == "technician"
    assert client.get("/api/v1/auth/me", headers=user_headers).status_code == 401
    event = db_session.query(AuditEvent).one()
    assert event.actor_id is None and event.action == "user.role_changed"
    assert event.details["reason"] == "Approved maintenance"
    assert not change(db_session, normal_user, "technician")["changed"]
    assert db_session.query(AuditEvent).count() == 1 and normal_user.token_version == 1


def test_role_change_cannot_demote_last_active_admin(db_session, admin_user, user_factory):
    inactive = user_factory("inactive_admin", role="admin")
    inactive.status = "suspended"
    db_session.commit()
    with pytest.raises(accounts.RoleChangeError, match="last active"):
        change(db_session, admin_user, "user")
    assert db_session.get(User, admin_user.id).role == "admin"


def test_role_change_preserves_farm_and_managed_user_invariants(db_session, manager_user, user_factory):
    member = user_factory("managed_role", created_by=manager_user.id)
    with pytest.raises(accounts.RoleChangeError, match="managed users"):
        change(db_session, manager_user, "technician")
    with pytest.raises(accounts.RoleChangeError, match="Managed user"):
        change(db_session, member, "admin")
    farm = Farm(owner_id=manager_user.id, name="Archived farm", archived_at=datetime.now(timezone.utc))
    db_session.add(farm)
    db_session.commit()
    with pytest.raises(accounts.RoleChangeError, match="owns Farms"):
        change(db_session, manager_user, "admin")


def test_role_change_blocks_membership_even_if_creator_missing(db_session, manager_user, normal_user):
    farm = Farm(owner_id=manager_user.id, name="Existing farm")
    db_session.add(farm)
    db_session.flush()
    db_session.add(FarmMember(farm_id=farm.id, user_id=normal_user.id))
    db_session.commit()
    with pytest.raises(accounts.RoleChangeError, match="Farm member"):
        change(db_session, normal_user, "technician")


def test_role_change_audit_failure_rolls_back(db_session, normal_user, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("audit unavailable")
    monkeypatch.setattr(accounts, "record_event", fail)
    with pytest.raises(RuntimeError):
        change(db_session, normal_user, "technician")
    assert db_session.get(User, normal_user.id).role == "user" and normal_user.token_version == 0


def test_concurrent_demotions_preserve_one_active_admin(db_session, user_factory):
    users = [user_factory(f"parallel_role_{i}", role="admin") for i in range(2)]
    names = [user.username for user in users]
    sessions = sessionmaker(bind=db_session.get_bind())
    def demote(name):
        with sessions() as db:
            try:
                accounts.change_role(db, username=name, role="user", reason="Concurrent maintenance", apply=True)
                return "changed"
            except accounts.RoleChangeError:
                return "refused"
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(demote, names)) == ["changed", "refused"]
    assert db_session.query(User).filter_by(role="admin", status="active").count() == 1


def test_stale_manager_cannot_create_farm_or_user_after_demotion(db_session, manager_user):
    with Session(db_session.get_bind()) as other:
        accounts.change_role(other, username=manager_user.username, role="technician",
                             reason="Changed responsibilities", apply=True)
    with pytest.raises(HTTPException) as error:
        create_farm(db_session, manager_user, FarmCreate(name="Race farm"))
    assert error.value.status_code == 403
    db_session.rollback()
    with pytest.raises(HTTPException):
        create_user_by(db_session, creator=manager_user,
                       data=ManagerCreateUserRequest(username="late_child", password="StrongPass123!"), role="user")
    assert db_session.query(Farm).count() == 0


def test_request_id_and_logs_do_not_include_query_body_or_unmatched_path(client, monkeypatch):
    from app.api import request_logging
    events = []
    monkeypatch.setattr(request_logging.logger, "info", events.append)
    response = client.get("/private-secret-path?token=secret-query", headers={"X-Request-ID": "forged"})
    assert response.status_code == 404
    assert len(response.headers["x-request-id"]) == 32 and response.headers["x-request-id"] != "forged"
    event = json.loads(events[-1])
    assert event["route"] == "unmatched" and event["request_id"] == response.headers["x-request-id"]
    assert event["status"] == 404 and event["duration_ms"] >= 0
    client.post("/api/v1/auth/login?token=secret-query", json={"username": "nonexistent", "password": "secret-body"})
    combined = "\n".join(events)
    assert all(value not in combined for value in ("secret-query", "secret-body", "private-secret-path", "nonexistent"))


def test_browser_can_read_request_id_and_retry_after(client, monkeypatch):
    monkeypatch.setattr(settings, "AUTH_REFRESH_RATE_LIMIT", 1)
    headers = {"Origin": settings.CORS_ORIGINS[0]}
    client.post("/api/v1/auth/refresh", headers=headers)
    response = client.post("/api/v1/auth/refresh", headers=headers)
    assert response.status_code == 429
    assert response.headers["access-control-allow-origin"] == settings.CORS_ORIGINS[0]
    assert {"x-request-id", "retry-after"} <= {
        item.strip().lower() for item in response.headers["access-control-expose-headers"].split(",")}


def test_unhandled_server_error_keeps_request_id_and_hides_details(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.api import request_logging
    isolated = FastAPI()
    isolated.add_middleware(request_logging.RequestLoggingMiddleware)
    isolated.add_exception_handler(Exception, request_logging.safe_server_error)
    @isolated.get("/broken")
    def broken():
        raise RuntimeError("secret exception details")
    events = []
    monkeypatch.setattr(request_logging.logger, "info", events.append)
    with TestClient(isolated, raise_server_exceptions=False) as client:
        response = client.get("/broken", headers={"Origin": settings.CORS_ORIGINS[0]})
    assert response.status_code == 500 and response.json() == {"detail": "Internal server error"}
    assert response.headers["x-request-id"] == json.loads(events[-1])["request_id"]
    assert response.headers["access-control-allow-origin"] == settings.CORS_ORIGINS[0]
    assert "secret exception details" not in "\n".join(events)
