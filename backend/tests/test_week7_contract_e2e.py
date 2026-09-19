"""API-only six-persona journey: real auth/database, synthetic inference output."""
import json
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.core.config import BASE_DIR
from app.core.release import API_VERSION, SCHEMA_REVISION
from app.main import app
from scripts.export_contract import contract_text, DEFAULT_OUTPUT
from tests.test_predict import mock_prediction, upload_dir, post_image  # noqa: F401


def login(client, username):
    result = client.post("/api/v1/auth/login", json={"username": username, "password": "StrongPass123!"})
    assert result.status_code == 200
    return {"Authorization": "Bearer " + result.json()["access_token"]}


def test_exported_contract_is_current():
    assert DEFAULT_OUTPUT.read_text(encoding="utf-8") == contract_text()
    schema = json.loads(contract_text())
    assert schema["info"]["version"] == API_VERSION
    operations = sum(method in {"get", "post", "put", "patch", "delete"}
                     for path, methods in schema["paths"].items() if path.startswith("/api/v1/")
                     for method in methods)
    assert operations == 41
    cfg = Config(str(BASE_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BASE_DIR / "alembic"))
    assert ScriptDirectory.from_config(cfg).get_heads() == [SCHEMA_REVISION]


def test_health_no_database_or_model_needed_for_liveness(client, monkeypatch):
    from app.api import health
    assert client.get("/health/live").json() == {"status": "alive"}
    monkeypatch.setattr(health, "database_ready", lambda: False)
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "scope": "database_schema_only"}
    monkeypatch.setattr(health, "database_ready", lambda: True)
    assert client.get("/health/ready").status_code == 200


def test_cors_preflight_and_error_contract(client):
    response = client.options("/api/v1/auth/refresh", headers={
        "Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-credentials"] == "true"
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    blocked = client.options("/api/v1/auth/refresh", headers={
        "Origin": "https://untrusted.invalid", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in blocked.headers
    assert isinstance(client.get("/api/v1/auth/me").json()["detail"], str)
    assert isinstance(client.post("/api/v1/auth/login", json={}).json()["detail"], list)


def test_docker_context_excludes_local_data_and_secrets():
    rules = set((BASE_DIR / ".dockerignore").read_text().splitlines())
    assert {".env", ".venv/", "backups/", "storage/uploads/*", "docs/"} <= rules
    assert "python:3.12-slim" in (BASE_DIR / "Dockerfile").read_text()


def test_frontend_examples_match_response_schemas():
    from app.schemas.user import UserResponse
    from app.schemas.farm import FarmResponse
    from app.schemas.disease_info import DiseaseInfoResponse
    from app.schemas.disease_proposal import ProposalResponse
    from app.schemas.stats import ScanStats
    from app.schemas.error import ApiError
    fixture = json.loads((BASE_DIR / "docs/week7/fixtures.json").read_text(encoding="utf-8"))
    assert fixture["api_version"] == API_VERSION
    examples = fixture["examples"]
    UserResponse.model_validate(examples["managed_user"])
    FarmResponse.model_validate(examples["farms_page"][0])
    DiseaseInfoResponse.model_validate(examples["disease_info"])
    ProposalResponse.model_validate(examples["proposal_pending"])
    ScanStats.model_validate(examples["scan_stats"])
    ApiError.model_validate(examples["error_403"])
    ApiError.model_validate(examples["error_422"])


def test_six_persona_journey(client, db_session, admin_user, mock_prediction, upload_dir):
    # The only pre-provisioned account is an Admin fixture; all other accounts
    # and domain changes below go through public API and real JWT dependencies.
    guest = post_image(client)
    assert guest.status_code == 200 and guest.json()["scan_id"] is None
    assert client.get("/api/v1/scans/history").status_code == 401
    public = client.post("/api/v1/auth/register", json={"username": "public_e2e", "password": "StrongPass123!"})
    assert public.status_code == 201 and public.json()["role"] == "user"
    user_headers = login(client, "public_e2e")
    assert client.get("/api/v1/farms", headers=user_headers).status_code == 403
    admin_headers = login(client, admin_user.username)
    for name, role in [("manager_e2e", "manager"), ("tech_e2e", "technician")]:
        assert client.post("/api/v1/admin/users", headers=admin_headers,
                           json={"username": name, "password": "StrongPass123!", "role": role}).status_code == 201
    manager_headers = login(client, "manager_e2e")
    tech_headers = login(client, "tech_e2e")
    farm_response = client.post("/api/v1/farms", headers=manager_headers, json={"name": "E2E Farm"})
    assert farm_response.status_code == 201
    farm_id = farm_response.json()["id"]
    members = []
    for index in range(2):
        member = client.post("/api/v1/manager/users", headers=manager_headers,
                             json={"username": f"managed_e2e_{index}", "password": "StrongPass123!"})
        assert member.status_code == 201
        members.append(member.json())
        assert client.post(f"/api/v1/farms/{farm_id}/members", headers=manager_headers,
                           json={"user_id": member.json()["id"]}).status_code == 201
    assert len(client.get(f"/api/v1/farms/{farm_id}/members", headers=manager_headers).json()) == 2
    managed_headers = login(client, members[0]["username"])
    assert client.get("/api/v1/me/farms", headers=managed_headers).json()[0]["id"] == farm_id
    assert client.post("/api/v1/manager/users", headers=manager_headers,
                       json={"username": "inject_e2e", "password": "StrongPass123!", "role": "admin"}).status_code == 422
    scan = post_image(client, headers=managed_headers, farm_id=farm_id)
    assert scan.status_code == 200 and scan.json()["farm_id"] == farm_id
    scan_id = scan.json()["scan_id"]
    assert client.get(f"/api/v1/scans/{scan_id}/image", headers=managed_headers).status_code == 200
    assert client.get(f"/api/v1/scans/{scan_id}", headers=manager_headers).status_code == 403
    assert client.get(f"/api/v1/scans/{scan_id}/image", headers=admin_headers).status_code == 403
    assert client.get(f"/api/v1/admin/scans/{scan_id}/image", headers=admin_headers).status_code == 200
    assert client.get(f"/api/v1/stats/farm/{farm_id}", headers=manager_headers).json()["total_scans"] == 1
    assert client.get("/api/v1/stats/admin/overview", headers=admin_headers).json()["total_scans"] == 1
    label = "Tomato___Early_blight"
    content = client.post("/api/v1/disease-info", headers=admin_headers,
                          json={"label_key": label, "disease_name": "Original"}).json()
    proposal = client.post("/api/v1/disease-proposals", headers=tech_headers,
                           json={"label_key": label, "disease_name": "Reviewed",
                                 "base_content_version": content["content_version"]})
    assert proposal.status_code == 201
    proposal_id = proposal.json()["id"]
    assert client.put(f"/api/v1/admin/disease-proposals/{proposal_id}/approve", headers=manager_headers).status_code == 403
    assert client.put(f"/api/v1/admin/disease-proposals/{proposal_id}/approve", headers=admin_headers).status_code == 200
    assert client.get(f"/api/v1/disease-info/{label}").json()["disease_name"] == "Reviewed"
    assert client.get("/api/v1/disease-proposals/mine", headers=tech_headers).json()[0]["status"] == "approved"
    assert client.patch(f"/api/v1/admin/users/{members[0]['id']}/status", headers=admin_headers,
                        json={"status": "suspended", "reason": "E2E control"}).status_code == 200
    assert client.get("/api/v1/scans/history", headers=managed_headers).status_code == 401
    assert client.get("/api/v1/auth/me", headers=user_headers).status_code == 200
