"""Weeks 5–6: account controls, oversight and content review without inference."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Barrier

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.security import create_refresh_token
from app.models import AuditEvent, DiseaseInfo, DiseaseProposal, Farm, User
from app.models import FarmMember
from app.services import proposal_service, user_admin_service
from app.schemas.user import UserStatusRequest
from tests.test_scans import create_scan


@pytest.fixture
def content(db_session):
    row = DiseaseInfo(label_key="Tomato___Early_blight", disease_name="Original", severity_level="medium")
    db_session.add(row)
    db_session.commit()
    return row


def proposal_payload(content):
    return {"label_key": content.label_key, "base_content_version": content.content_version,
            "disease_name": "Reviewed content", "description": "Symptoms", "treatment": "Care",
            "severity_level": "high"}


def test_suspend_and_resume_revoke_sessions(client, db_session, admin_headers, normal_user, user_headers):
    old_refresh = create_refresh_token(normal_user.id, normal_user.token_version)
    url = f"/api/v1/admin/users/{normal_user.id}/status"
    data = {"status": "suspended", "reason": "Security review"}
    assert client.patch(url, headers=user_headers, json=data).status_code == 403
    assert client.patch(url, headers=admin_headers, json={**data, "reason": " "}).status_code == 422
    response = client.patch(url, headers=admin_headers, json=data)
    assert response.status_code == 200 and response.json()["status"] == "suspended"
    assert client.get("/api/v1/auth/me", headers=user_headers).status_code == 401
    assert client.post("/api/v1/auth/login", json={"username": normal_user.username,
                       "password": "StrongPass123!"}).status_code == 401
    client.cookies.set(settings.REFRESH_COOKIE_NAME, old_refresh)
    assert client.post("/api/v1/auth/refresh").status_code == 401
    assert client.patch(url, headers=admin_headers, json=data).status_code == 200
    assert db_session.query(AuditEvent).filter_by(action="user.status_changed").count() == 1
    assert client.patch(url, headers=admin_headers, json={"status": "active", "reason": "Resolved"}).status_code == 200
    assert client.get("/api/v1/auth/me", headers=user_headers).status_code == 401
    assert client.post("/api/v1/auth/refresh").status_code == 401
    assert client.post("/api/v1/auth/login", json={"username": normal_user.username,
                       "password": "StrongPass123!"}).status_code == 200
    events = db_session.query(AuditEvent).all()
    assert len(events) == 2
    assert all("password" not in str(event.details) for event in events)


def test_admin_cannot_suspend_self(client, admin_user, admin_headers):
    assert client.patch(f"/api/v1/admin/users/{admin_user.id}/status", headers=admin_headers,
                        json={"status": "suspended", "reason": "test"}).status_code == 409


def test_concurrent_admin_cross_suspension_keeps_active_admin(db_session, user_factory):
    admins = [user_factory("admin_a", role="admin"), user_factory("admin_b", role="admin")]
    ids = [u.id for u in admins]
    engine = db_session.get_bind()
    barrier = Barrier(2)

    def suspend(i):
        with Session(engine) as db:
            actor = db.get(User, ids[i])
            barrier.wait(timeout=10)
            try:
                user_admin_service.set_user_status(db, actor=actor, user_id=ids[1-i],
                                                   data=UserStatusRequest(status="suspended", reason="review"))
                return 200
            except HTTPException as exc:
                db.rollback()
                return exc.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(suspend, range(2)))
    assert sorted(results) == [200, 403]
    db_session.expire_all()
    assert db_session.query(User).filter_by(role="admin", status="active").count() == 1


def test_proposal_approve_atomic_and_idempotent(client, db_session, content, technician_headers, admin_headers):
    response = client.post("/api/v1/disease-proposals", headers=technician_headers, json=proposal_payload(content))
    assert response.status_code == 201
    proposal = response.json()
    assert proposal["status"] == "pending"
    url = f"/api/v1/admin/disease-proposals/{proposal['id']}"
    approved = client.put(url + "/approve", headers=admin_headers)
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    db_session.refresh(content)
    assert content.content_version == 2 and content.disease_name == "Reviewed content"
    assert client.put(url + "/approve", headers=admin_headers).json() == approved.json()
    assert client.put(url + "/reject", headers=admin_headers, json={"review_note": "No"}).status_code == 409
    assert db_session.query(AuditEvent).filter_by(action="proposal.approved").count() == 1


def test_reject_note_required_and_no_content_change(client, db_session, content, technician_headers, admin_headers):
    proposal = client.post("/api/v1/disease-proposals", headers=technician_headers, json=proposal_payload(content)).json()
    url = f"/api/v1/admin/disease-proposals/{proposal['id']}/reject"
    assert client.put(url, headers=admin_headers, json={"review_note": " "}).status_code == 422
    result = client.put(url, headers=admin_headers, json={"review_note": "Needs references"})
    assert result.status_code == 200
    assert client.put(url, headers=admin_headers, json={"review_note": "Replacement"}).json() == result.json()
    db_session.refresh(content)
    assert content.content_version == 1 and content.disease_name == "Original"


@pytest.mark.parametrize("mutation", ["update", "archive", "restore"])
def test_stale_proposal_conflict(client, content, technician_headers, admin_headers, mutation):
    payload = proposal_payload(content)
    proposal = client.post("/api/v1/disease-proposals", headers=technician_headers, json=payload).json()
    if mutation == "update":
        assert client.put(f"/api/v1/disease-info/{content.label_key}", headers=admin_headers,
                          json={"treatment": "Newer treatment"}).status_code == 200
    else:
        assert client.delete(f"/api/v1/disease-info/{content.label_key}", headers=admin_headers).status_code == 204
        if mutation == "restore":
            assert client.post("/api/v1/disease-info", headers=admin_headers,
                               json={"label_key": content.label_key, "disease_name": "Restored"}).status_code == 201
    assert client.put(f"/api/v1/admin/disease-proposals/{proposal['id']}/approve", headers=admin_headers).status_code == 409


def test_proposal_permissions_mine_filters(client, content, technician_headers, admin_headers,
                                          user_headers, user_factory, token_headers):
    payload = proposal_payload(content)
    for headers in [admin_headers, user_headers]:
        assert client.post("/api/v1/disease-proposals", headers=headers, json=payload).status_code == 403
    assert client.post("/api/v1/disease-proposals", headers=technician_headers,
                       json={**payload, "reviewer_id": 1}).status_code == 422
    assert client.post("/api/v1/disease-proposals", headers=technician_headers,
                       json={**payload, "label_key": "new_unknown"}).status_code == 404
    assert client.post("/api/v1/disease-proposals", headers=technician_headers,
                       json={**payload, "base_content_version": 99}).status_code == 409
    assert client.post("/api/v1/disease-proposals", headers=technician_headers, json=payload).status_code == 201
    other = user_factory("other_tech", role="technician")
    assert client.get("/api/v1/disease-proposals/mine", headers=token_headers(other)).json() == []
    assert len(client.get("/api/v1/disease-proposals/mine?status=pending", headers=technician_headers).json()) == 1
    assert client.get("/api/v1/admin/disease-proposals", headers=technician_headers).status_code == 403
    assert len(client.get("/api/v1/admin/disease-proposals?status=pending", headers=admin_headers).json()) == 1
    assert client.get("/api/v1/admin/disease-proposals?status=invalid", headers=admin_headers).status_code == 422


def test_concurrent_proposals_same_revision_only_one_applies(db_session, client, content,
                                                           technician_headers, admin_user):
    payload = proposal_payload(content)
    ids = [client.post("/api/v1/disease-proposals", headers=technician_headers, json=payload).json()["id"] for _ in range(2)]
    actor_id = admin_user.id
    engine = db_session.get_bind()
    barrier = Barrier(2)

    def approve(proposal_id):
        with Session(engine) as db:
            actor = db.get(User, actor_id)
            barrier.wait(timeout=10)
            try:
                proposal_service.review(db, actor, proposal_id, approve=True)
                return 200
            except HTTPException as exc:
                db.rollback()
                return exc.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(approve, ids))
    assert sorted(results) == [200, 409]
    db_session.refresh(content)
    assert content.content_version == 2
    assert db_session.query(DiseaseProposal).filter_by(status="approved").count() == 1


def test_review_audit_failure_rolls_back_content(db_session, client, content, technician_headers,
                                               admin_user, monkeypatch):
    proposal_id = client.post("/api/v1/disease-proposals", headers=technician_headers,
                              json=proposal_payload(content)).json()["id"]
    def fail_audit(*args, **kwargs):
        raise RuntimeError("simulated audit failure")
    monkeypatch.setattr(proposal_service, "record_event", fail_audit)
    with Session(db_session.get_bind()) as db:
        actor = db.get(User, admin_user.id)
        with pytest.raises(RuntimeError):
            proposal_service.review(db, actor, proposal_id, approve=True)
        db.rollback()
    db_session.refresh(content)
    assert content.content_version == 1
    assert db_session.get(DiseaseProposal, proposal_id).status == "pending"


def test_stats_ownership_counts_and_time_boundaries(client, db_session, manager_user, normal_user,
                                                  manager_headers, admin_headers, other_manager_user,
                                                  token_headers):
    farm = Farm(name="Stats", owner_id=manager_user.id)
    db_session.add(farm)
    db_session.commit()
    for i in range(4):
        scan = create_scan(db_session, normal_user.id, f"stats-{i}")
        scan.farm_id = farm.id
        scan.created_at = datetime(2026, 9, 15, i, 0)
        if i == 1:
            scan.validation_status = "ambiguous"
            scan.is_valid_leaf = False
        if i == 2:
            scan.inference_mode = "legacy"
        db_session.commit()
    url = f"/api/v1/stats/farm/{farm.id}"
    assert client.get(url, headers=admin_headers).status_code == 403
    assert client.get(url, headers=token_headers(other_manager_user)).status_code == 403
    params = {"from": "2026-09-15T07:00:00+07:00", "to": "2026-09-15T10:00:00+07:00"}
    result = client.get(url, headers=manager_headers, params=params).json()
    assert result["total_scans"] == 3
    assert result["accepted_scans"] == result["rejected_scans"] == result["legacy_scans"] == 1
    assert result["rejection_rate"] == 0.5
    assert result["disease_counts"] == [{"label_key": "Tomato___Early_blight", "count": 1}]
    overview = client.get("/api/v1/stats/admin/overview", headers=admin_headers).json()
    assert overview["total_scans"] == 4 and overview["total_farms"] == 1
    recent = client.get("/api/v1/stats/admin/recent-invalid", headers=admin_headers).json()
    assert len(recent) == 1 and recent[0]["validation_status"] == "ambiguous"
    assert client.get(url, headers=manager_headers, params={"from": "2026-09-15T00:00:00"}).status_code == 422
    assert client.get(url, headers=manager_headers, params={"from": params["to"], "to": params["from"]}).status_code == 422


def test_empty_stats(client, admin_headers):
    result = client.get("/api/v1/stats/admin/overview", headers=admin_headers).json()
    assert result["total_scans"] == 0 and result["rejection_rate"] is None
    assert result["disease_counts"] == []


def test_admin_scans_separate_namespace_and_audit(client, db_session, normal_user,
                                                admin_headers, user_headers, tmp_path, monkeypatch):
    scan = create_scan(db_session, normal_user.id, "monitor")
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    (tmp_path / "monitor.jpg").write_bytes(b"image")
    assert client.get("/api/v1/admin/scans", headers=user_headers).status_code == 403
    assert client.get(f"/api/v1/scans/{scan.id}/image", headers=admin_headers).status_code == 403
    result = client.get("/api/v1/admin/scans", headers=admin_headers,
                        params={"user_id": normal_user.id, "limit": 1}).json()
    assert result[0]["id"] == scan.id and result[0]["user_id"] == normal_user.id
    assert client.get("/api/v1/admin/scans?validation_status=ambiguous", headers=admin_headers).json() == []
    response = client.get(f"/api/v1/admin/scans/{scan.id}/image", headers=admin_headers)
    assert response.status_code == 200 and response.content == b"image"
    assert response.headers["cache-control"] == "private, no-store"
    assert db_session.query(AuditEvent).filter_by(action="scan.image_access_authorized").count() == 1


@pytest.mark.parametrize("url", ["/api/v1/admin/users", "/api/v1/manager/users",
                                  "/api/v1/admin/scans", "/api/v1/admin/disease-proposals",
                                  "/api/v1/stats/admin/recent-invalid"])
def test_new_lists_pagination_bounds(client, admin_headers, manager_headers, url):
    headers = manager_headers if "/manager/" in url else admin_headers
    assert client.get(url + "?limit=101", headers=headers).status_code == 422
    assert client.get(url + "?offset=-1", headers=headers).status_code == 422


def test_member_pagination_and_suspended_assignment(client, db_session, manager_user, manager_headers,
                                                   user_factory, admin_headers):
    farm = Farm(name="Members", owner_id=manager_user.id)
    db_session.add(farm)
    db_session.commit()
    users = [user_factory(f"member_{i}", created_by=manager_user.id) for i in range(3)]
    url = f"/api/v1/farms/{farm.id}/members"
    for user in users[:2]:
        assert client.post(url, headers=manager_headers, json={"user_id": user.id}).status_code == 201
    assert len(client.get(url + "?limit=1&offset=1", headers=manager_headers).json()) == 1
    assert client.get(url + "?limit=101", headers=manager_headers).status_code == 422
    client.patch(f"/api/v1/admin/users/{users[2].id}/status", headers=admin_headers,
                  json={"status": "suspended", "reason": "Review"})
    assert client.post(url, headers=manager_headers, json={"user_id": users[2].id}).status_code == 409


def test_farm_assignment_rechecks_creator_and_membership(db_session, manager_user, other_manager_user, user_factory):
    from app.services.prediction_workflow_service import _resolve_farm
    member = user_factory("managed_scope", created_by=manager_user.id)
    farm = Farm(name="Other manager", owner_id=other_manager_user.id)
    db_session.add(farm)
    db_session.flush()
    db_session.add(FarmMember(farm_id=farm.id, user_id=member.id))
    db_session.commit()
    assert _resolve_farm(db_session, member, farm.id)[1] == "not_allowed"


def test_direct_provisioning_service_cannot_escalate(db_session, manager_user):
    from app.schemas.user import ManagerCreateUserRequest
    data = ManagerCreateUserRequest(username="injected", password="StrongPass123!")
    with pytest.raises(HTTPException) as exc:
        user_admin_service.create_user_by(db_session, creator=manager_user, data=data, role="admin")
    assert exc.value.status_code == 403


def test_admin_image_audit_failure_does_not_return_image(client, db_session, normal_user, admin_headers,
                                                       tmp_path, monkeypatch):
    from app.api.v1.endpoints import monitoring
    scan = create_scan(db_session, normal_user.id, "audit-failure")
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    (tmp_path / "audit-failure.jpg").write_bytes(b"private")
    def fail_audit(*args, **kwargs):
        raise RuntimeError("simulated audit failure")
    monkeypatch.setattr(monitoring, "record_event", fail_audit)
    with pytest.raises(RuntimeError, match="simulated audit failure"):
        client.get(f"/api/v1/admin/scans/{scan.id}/image", headers=admin_headers)
    db_session.rollback()
    assert db_session.query(AuditEvent).count() == 0


def test_revoked_account_during_request_does_not_persist_scan(client, db_session, normal_user,
                                                            user_headers, active_model_versions,
                                                            tmp_path, monkeypatch):
    from app.models import Scan
    from app.services.predict_service import predict_service
    from tests.test_predict import make_result, create_dummy_image
    user_id = normal_user.id
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))

    def fake_predict(_data, specs, mode):
        # Simulate concurrent account suspension, without executing a model.
        with Session(db_session.get_bind()) as other:
            other.query(User).filter(User.id == user_id).update(
                {User.status: "suspended", User.token_version: User.token_version + 1})
            other.commit()
        return make_result(specs, mode)

    monkeypatch.setattr(predict_service, "predict", fake_predict)
    result = client.post("/api/v1/predict", headers=user_headers,
                         files={"file": ("leaf.jpg", create_dummy_image(), "image/jpeg")})
    assert result.status_code == 401
    assert db_session.query(Scan).count() == 0
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("statement", [
    "UPDATE users SET status='unknown'",
    "UPDATE users SET token_version=-1",
    "UPDATE disease_info SET content_version=0",
])
def test_new_database_constraints(db_session, normal_user, content, statement):
    with pytest.raises(IntegrityError):
        db_session.execute(text(statement))
        db_session.commit()
    db_session.rollback()


def test_concurrent_approve_same_proposal_is_idempotent(client, db_session, content,
                                                      technician_headers, admin_user):
    proposal_id = client.post("/api/v1/disease-proposals", headers=technician_headers,
                              json=proposal_payload(content)).json()["id"]
    engine = db_session.get_bind()
    actor_id = admin_user.id
    barrier = Barrier(2)
    def approve(_):
        with Session(engine) as db:
            actor = db.get(User, actor_id)
            barrier.wait(timeout=10)
            return proposal_service.review(db, actor, proposal_id, approve=True).status
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(approve, range(2))) == ["approved", "approved"]
    db_session.refresh(content)
    assert content.content_version == 2
    assert db_session.query(AuditEvent).filter_by(action="proposal.approved").count() == 1
