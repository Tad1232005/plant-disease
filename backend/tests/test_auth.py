"""Kiểm thử Auth/JWT/RBAC của Tuần 1."""

from datetime import datetime, timezone

from app.core.config import settings
from app.core.security import decode_token
from app.models import User


REGISTER_PAYLOAD = {
    "username": "new_farmer",
    "email": "farmer@example.com",
    "password": "StrongPass123!",
    "full_name": "Nông dân mới",
}


def register(client, payload: dict | None = None):
    return client.post(
        "/api/v1/auth/register",
        json=payload or REGISTER_PAYLOAD,
    )


def login(client):
    return client.post(
        "/api/v1/auth/login",
        json={
            "username": REGISTER_PAYLOAD["username"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )


def test_register_returns_safe_user_and_defaults(client, db_session):
    response = register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["role"] == "user"
    assert body["created_by"] is None
    assert "password" not in body
    assert "password_hash" not in body

    user = db_session.query(User).filter_by(username="new_farmer").one()
    assert user.token_version == 0
    assert user.password_hash != REGISTER_PAYLOAD["password"]


def test_register_rejects_duplicate_username_and_email(client):
    assert register(client).status_code == 201

    duplicate_username = {**REGISTER_PAYLOAD, "email": "other@example.com"}
    assert register(client, duplicate_username).status_code == 400

    duplicate_email = {**REGISTER_PAYLOAD, "username": "other_farmer"}
    assert register(client, duplicate_email).status_code == 400


def test_login_sets_http_only_refresh_cookie_and_access_ttl(client):
    register(client)
    response = login(client)

    assert response.status_code == 200
    access_token = response.json()["access_token"]
    payload = decode_token(access_token)
    assert payload["type"] == "access"
    assert payload["role"] == "user"
    ttl_minutes = (
        datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        - datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
    ).total_seconds() / 60
    assert ttl_minutes == settings.ACCESS_TOKEN_EXPIRE_MINUTES

    set_cookie = response.headers["set-cookie"].lower()
    assert "httponly" in set_cookie
    assert f"path={settings.REFRESH_COOKIE_PATH}".lower() in set_cookie
    refresh_token = client.cookies.get(settings.REFRESH_COOKIE_NAME)
    assert refresh_token
    refresh_payload = decode_token(refresh_token)
    assert refresh_payload["type"] == "refresh"
    assert refresh_payload["token_version"] == 0
    refresh_ttl_days = (
        datetime.fromtimestamp(refresh_payload["exp"], tz=timezone.utc)
        - datetime.fromtimestamp(refresh_payload["iat"], tz=timezone.utc)
    ).total_seconds() / (24 * 60 * 60)
    assert refresh_ttl_days == settings.REFRESH_TOKEN_EXPIRE_DAYS


def test_login_rejects_wrong_password(client):
    register(client)
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "new_farmer", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_me_requires_access_token(client):
    register(client)
    access_token = login(client).json()["access_token"]

    assert client.get("/api/v1/auth/me").status_code == 401
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["username"] == "new_farmer"


def test_me_rejects_refresh_token_as_bearer(client):
    register(client)
    login(client)
    refresh_token = client.cookies.get(settings.REFRESH_COOKIE_NAME)

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )

    assert response.status_code == 401


def test_refresh_rotates_cookie(client):
    register(client)
    login(client)
    old_refresh = client.cookies.get(settings.REFRESH_COOKIE_NAME)

    response = client.post("/api/v1/auth/refresh")

    assert response.status_code == 200
    assert decode_token(response.json()["access_token"])["type"] == "access"
    assert client.cookies.get(settings.REFRESH_COOKIE_NAME) != old_refresh


def test_logout_revokes_old_refresh_token(client, db_session):
    register(client)
    login_response = login(client)
    access_token = login_response.json()["access_token"]
    old_refresh = client.cookies.get(settings.REFRESH_COOKIE_NAME)

    logout_response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert logout_response.status_code == 204
    user = db_session.query(User).filter_by(username="new_farmer").one()
    assert user.token_version == 1

    client.cookies.set(
        settings.REFRESH_COOKIE_NAME,
        old_refresh,
        path=settings.REFRESH_COOKIE_PATH,
    )
    assert client.post("/api/v1/auth/refresh").status_code == 401


def test_refresh_requires_cookie(client):
    assert client.post("/api/v1/auth/refresh").status_code == 401
