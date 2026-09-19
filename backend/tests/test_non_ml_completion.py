"""Regression coverage for backend tasks independent of ML artifacts."""
import pytest

from app.core.config import settings
from app.core.security import create_refresh_token
from app.models import Farm, FarmMember
from tests.test_scans import create_scan


def test_password_change_revokes_all_tokens(client, normal_user, user_headers):
    old_refresh = create_refresh_token(normal_user.id, normal_user.token_version)
    payload = {"current_password": "StrongPass123!", "new_password": "NewStrongPass456!"}
    assert client.post("/api/v1/auth/change-password", json=payload).status_code == 401
    assert client.post("/api/v1/auth/change-password", headers=user_headers,
                       json={**payload, "current_password": "wrong"}).status_code == 400
    assert client.post("/api/v1/auth/change-password", headers=user_headers,
                       json={**payload, "new_password": "weak"}).status_code == 422
    response = client.post("/api/v1/auth/change-password", headers=user_headers, json=payload)
    assert response.status_code == 204
    assert "Max-Age=0" in response.headers["set-cookie"]
    assert client.get("/api/v1/auth/me", headers=user_headers).status_code == 401
    client.cookies.set(settings.REFRESH_COOKIE_NAME, old_refresh)
    assert client.post("/api/v1/auth/refresh").status_code == 401
    assert client.post("/api/v1/auth/login", json={"username": normal_user.username,
                        "password": "StrongPass123!"}).status_code == 401
    assert client.post("/api/v1/auth/login", json={"username": normal_user.username,
                        "password": payload["new_password"]}).status_code == 200


def test_my_farms_membership_and_archive(client, db_session, manager_user, other_manager_user,
                                        user_factory, token_headers, admin_headers):
    member = user_factory("managed_choice", created_by=manager_user.id)
    farms = [Farm(name="own", owner_id=manager_user.id),
             Farm(name="foreign", owner_id=other_manager_user.id)]
    db_session.add_all(farms)
    db_session.flush()
    db_session.add_all([FarmMember(farm_id=f.id, user_id=member.id) for f in farms])
    db_session.commit()
    headers = token_headers(member)
    assert client.get("/api/v1/me/farms").status_code == 401
    assert client.get("/api/v1/me/farms", headers=admin_headers).json() == []
    assert [f["id"] for f in client.get("/api/v1/me/farms", headers=headers).json()] == [farms[0].id]
    assert client.get("/api/v1/farms", headers=headers).status_code == 403
    assert client.delete(f"/api/v1/farms/{farms[0].id}", headers=token_headers(manager_user)).status_code == 204
    assert client.get("/api/v1/me/farms", headers=headers).json() == []


def test_private_image_owner_missing_and_traversal(client, db_session, normal_user,
                                                  user_headers, admin_headers, tmp_path, monkeypatch):
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(uploads))
    scan = create_scan(db_session, normal_user.id, "private-image")
    url = f"/api/v1/scans/{scan.id}/image"
    assert client.get(url).status_code == 401
    assert client.get(url, headers=admin_headers).status_code == 403
    assert client.get(url, headers=user_headers).status_code == 404
    (uploads / "private-image.jpg").write_bytes(b"test-image")
    response = client.get(url, headers=user_headers)
    assert response.status_code == 200
    assert response.content == b"test-image"
    assert response.headers["cache-control"] == "private, no-store"
    (tmp_path / "outside.jpg").write_bytes(b"private")
    scan.image_path = "storage/uploads/../outside.jpg"
    db_session.commit()
    assert client.get(url, headers=user_headers).status_code == 404


@pytest.mark.parametrize("payload", [{"name": None}, {"owner_id": 123}, {"name": "   "}])
def test_farm_update_rejects_invalid_fields(client, manager_headers, payload):
    farm = client.post("/api/v1/farms", headers=manager_headers, json={"name": "Farm"}).json()
    url = f"/api/v1/farms/{farm['id']}"
    assert client.put(url, headers=manager_headers, json=payload).status_code == 422
    assert client.put(url, headers=manager_headers, json={"location_text": None}).status_code == 200
    assert client.get(url, headers=manager_headers).json()["name"] == "Farm"


@pytest.mark.parametrize("payload", [{"disease_name": None}, {"severity_level": None}, {"label_key": "changed"}])
def test_disease_update_rejects_invalid_fields(client, admin_headers, payload):
    assert client.post("/api/v1/disease-info", headers=admin_headers,
                       json={"label_key": "test", "disease_name": "Test"}).status_code == 201
    assert client.put("/api/v1/disease-info/test", headers=admin_headers, json=payload).status_code == 422
    response = client.put("/api/v1/disease-info/test", headers=admin_headers, json={"treatment": None})
    assert response.status_code == 200
    assert response.json()["disease_name"] == "Test"


def test_list_pagination(client, manager_headers, admin_headers):
    for name in ["aaa", "bbb", "ccc"]:
        client.post("/api/v1/farms", headers=manager_headers, json={"name": name})
        client.post("/api/v1/disease-info", headers=admin_headers,
                    json={"label_key": name, "disease_name": name})
    for url in ["/api/v1/farms", "/api/v1/disease-info", "/api/v1/me/farms"]:
        response = client.get(url + "?limit=1&offset=1", headers=manager_headers)
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert client.get(url + "?limit=101", headers=manager_headers).status_code == 422
        assert client.get(url + "?offset=-1", headers=manager_headers).status_code == 422
