"""Test Disease Proposal workflow: submit, list, review (approve/reject), role isolation."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.disease_info import DiseaseInfo
from app.models.disease_proposal import DiseaseProposal
from app.models.user import User


@pytest.fixture
def existing_disease(db_session: Session) -> DiseaseInfo:
    disease = DiseaseInfo(
        label_key="Tomato___Early_blight",
        disease_name="Bệnh đốm vòng cà chua",
        description="Vết đốm màu nâu đen hình tròn đồng tâm trên lá già.",
        treatment="Cắt tỉa lá bệnh, phun thuốc gốc đồng.",
        severity_level="medium",
        content_version=1,
        is_active=True,
    )
    db_session.add(disease)
    db_session.commit()
    db_session.refresh(disease)
    return disease


class TestSubmitProposal:
    def test_technician_can_submit_proposal(
        self, client: TestClient, technician_headers, existing_disease
    ):
        r = client.post(
            "/api/v1/disease-proposals",
            headers=technician_headers,
            json={
                "label_key": existing_disease.label_key,
                "disease_name": "Đốm vòng cà chua cập nhật",
                "severity_level": "high",
                "description": "Triệu chứng chi tiết hơn...",
                "treatment": "Phun thuốc gốc đồng kết hợp luân canh.",
                "base_content_version": existing_disease.content_version,
            },
        )
        assert r.status_code == 201
        body = r.json()
        assert body["label_key"] == existing_disease.label_key
        assert body["status"] == "pending"
        assert body["disease_name"] == "Đốm vòng cà chua cập nhật"
        assert body["id"] is not None

    def test_submit_nonexistent_disease_404(
        self, client: TestClient, technician_headers
    ):
        r = client.post(
            "/api/v1/disease-proposals",
            headers=technician_headers,
            json={
                "label_key": "Nonexistent___Disease",
                "disease_name": "Unknown",
                "base_content_version": 1,
            },
        )
        assert r.status_code == 404

    def test_submit_version_mismatch_409(
        self, client: TestClient, technician_headers, existing_disease
    ):
        r = client.post(
            "/api/v1/disease-proposals",
            headers=technician_headers,
            json={
                "label_key": existing_disease.label_key,
                "disease_name": "New name",
                "base_content_version": 999,  # Mismatch with version 1
            },
        )
        assert r.status_code == 409

    def test_user_cannot_submit_proposal(
        self, client: TestClient, user_headers, existing_disease
    ):
        r = client.post(
            "/api/v1/disease-proposals",
            headers=user_headers,
            json={
                "label_key": existing_disease.label_key,
                "disease_name": "New name",
                "base_content_version": existing_disease.content_version,
            },
        )
        assert r.status_code == 403

    def test_manager_cannot_submit_proposal(
        self, client: TestClient, manager_headers, existing_disease
    ):
        r = client.post(
            "/api/v1/disease-proposals",
            headers=manager_headers,
            json={
                "label_key": existing_disease.label_key,
                "disease_name": "New name",
                "base_content_version": existing_disease.content_version,
            },
        )
        assert r.status_code == 403

    def test_admin_cannot_submit_proposal(
        self, client: TestClient, admin_headers, existing_disease
    ):
        """Technician-only: Admin cannot directly submit proposals."""
        r = client.post(
            "/api/v1/disease-proposals",
            headers=admin_headers,
            json={
                "label_key": existing_disease.label_key,
                "disease_name": "New name",
                "base_content_version": existing_disease.content_version,
            },
        )
        assert r.status_code == 403

    def test_unauthenticated_cannot_submit(self, client: TestClient, existing_disease):
        r = client.post(
            "/api/v1/disease-proposals",
            json={
                "label_key": existing_disease.label_key,
                "disease_name": "New name",
                "base_content_version": 1,
            },
        )
        assert r.status_code == 401


class TestMyProposals:
    def test_technician_can_list_own_proposals(
        self, client: TestClient, technician_headers, existing_disease
    ):
        # Create a proposal first
        client.post(
            "/api/v1/disease-proposals",
            headers=technician_headers,
            json={
                "label_key": existing_disease.label_key,
                "disease_name": "My proposal",
                "base_content_version": existing_disease.content_version,
            },
        )
        r = client.get("/api/v1/disease-proposals/mine", headers=technician_headers)
        assert r.status_code == 200
        items = r.json()
        assert len(items) >= 1
        assert items[0]["disease_name"] == "My proposal"

    def test_non_technician_cannot_access_mine(self, client: TestClient, user_headers):
        r = client.get("/api/v1/disease-proposals/mine", headers=user_headers)
        assert r.status_code == 403


class TestAdminProposals:
    def test_admin_can_list_all_proposals(
        self, client: TestClient, admin_headers, technician_headers, existing_disease
    ):
        client.post(
            "/api/v1/disease-proposals",
            headers=technician_headers,
            json={
                "label_key": existing_disease.label_key,
                "disease_name": "Admin review proposal",
                "base_content_version": existing_disease.content_version,
            },
        )
        r = client.get("/api/v1/admin/disease-proposals", headers=admin_headers)
        assert r.status_code == 200
        items = r.json()
        assert len(items) >= 1

    def test_admin_filter_by_status(
        self, client: TestClient, admin_headers, technician_headers, existing_disease
    ):
        client.post(
            "/api/v1/disease-proposals",
            headers=technician_headers,
            json={
                "label_key": existing_disease.label_key,
                "disease_name": "Status filter proposal",
                "base_content_version": existing_disease.content_version,
            },
        )
        r = client.get("/api/v1/admin/disease-proposals?status=pending", headers=admin_headers)
        assert r.status_code == 200
        for item in r.json():
            assert item["status"] == "pending"

    def test_non_admin_cannot_list_admin_proposals(
        self, client: TestClient, technician_headers
    ):
        r = client.get("/api/v1/admin/disease-proposals", headers=technician_headers)
        assert r.status_code == 403


class TestApproveProposal:
    def test_admin_can_approve(
        self, client: TestClient, admin_headers, technician_headers, existing_disease
    ):
        p = client.post(
            "/api/v1/disease-proposals",
            headers=technician_headers,
            json={
                "label_key": existing_disease.label_key,
                "disease_name": "Approved name",
                "treatment": "New treatment",
                "base_content_version": existing_disease.content_version,
            },
        ).json()

        pid = p["id"]
        r = client.put(f"/api/v1/admin/disease-proposals/{pid}/approve", headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["status"] == "approved"

        # Check disease_info was updated
        info = client.get(f"/api/v1/disease-info/{existing_disease.label_key}").json()
        assert info["disease_name"] == "Approved name"
        assert info["treatment"] == "New treatment"
        assert info["content_version"] == 2

    def test_approve_idempotent(
        self, client: TestClient, admin_headers, technician_headers, existing_disease
    ):
        p = client.post(
            "/api/v1/disease-proposals",
            headers=technician_headers,
            json={
                "label_key": existing_disease.label_key,
                "disease_name": "Idempotent approve",
                "base_content_version": existing_disease.content_version,
            },
        ).json()
        pid = p["id"]
        client.put(f"/api/v1/admin/disease-proposals/{pid}/approve", headers=admin_headers)
        r2 = client.put(f"/api/v1/admin/disease-proposals/{pid}/approve", headers=admin_headers)
        assert r2.status_code == 200
        assert r2.json()["status"] == "approved"

    def test_technician_cannot_approve(
        self, client: TestClient, technician_headers, existing_disease
    ):
        p = client.post(
            "/api/v1/disease-proposals",
            headers=technician_headers,
            json={
                "label_key": existing_disease.label_key,
                "disease_name": "Forbidden approve",
                "base_content_version": existing_disease.content_version,
            },
        ).json()
        pid = p["id"]
        r = client.put(f"/api/v1/admin/disease-proposals/{pid}/approve", headers=technician_headers)
        assert r.status_code == 403


class TestRejectProposal:
    def test_admin_can_reject_with_note(
        self, client: TestClient, admin_headers, technician_headers, existing_disease
    ):
        p = client.post(
            "/api/v1/disease-proposals",
            headers=technician_headers,
            json={
                "label_key": existing_disease.label_key,
                "disease_name": "To be rejected",
                "base_content_version": existing_disease.content_version,
            },
        ).json()
        pid = p["id"]
        r = client.put(
            f"/api/v1/admin/disease-proposals/{pid}/reject",
            headers=admin_headers,
            json={"review_note": "Thông tin chưa chính xác, cần kiểm tra lại."},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "rejected"
        assert body["review_note"] == "Thông tin chưa chính xác, cần kiểm tra lại."

    def test_reject_without_note_422(
        self, client: TestClient, admin_headers, technician_headers, existing_disease
    ):
        p = client.post(
            "/api/v1/disease-proposals",
            headers=technician_headers,
            json={
                "label_key": existing_disease.label_key,
                "disease_name": "No note reject",
                "base_content_version": existing_disease.content_version,
            },
        ).json()
        pid = p["id"]
        r = client.put(
            f"/api/v1/admin/disease-proposals/{pid}/reject",
            headers=admin_headers,
            json={"review_note": ""},
        )
        assert r.status_code == 422

    def test_cannot_reject_already_approved_409(
        self, client: TestClient, admin_headers, technician_headers, existing_disease
    ):
        p = client.post(
            "/api/v1/disease-proposals",
            headers=technician_headers,
            json={
                "label_key": existing_disease.label_key,
                "disease_name": "Approve first",
                "base_content_version": existing_disease.content_version,
            },
        ).json()
        pid = p["id"]
        client.put(f"/api/v1/admin/disease-proposals/{pid}/approve", headers=admin_headers)
        r = client.put(
            f"/api/v1/admin/disease-proposals/{pid}/reject",
            headers=admin_headers,
            json={"review_note": "Try to reject approved"},
        )
        assert r.status_code == 409
