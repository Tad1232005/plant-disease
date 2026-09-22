"""Test Model Version API — list, register, activate, ownership guard."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# List / Detail (read-only, Admin only)
# ---------------------------------------------------------------------------


class TestListModelVersions:
    def test_admin_can_list(self, client: TestClient, admin_headers, active_model_versions):
        r = client.get("/api/v1/admin/model-versions", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        # Fixture tạo 3 version inactive-free test versions
        assert len(data) >= 3

    def test_list_filter_is_active_true(self, client: TestClient, admin_headers, active_model_versions):
        r = client.get("/api/v1/admin/model-versions?is_active=true", headers=admin_headers)
        assert r.status_code == 200
        for item in r.json():
            assert item["is_active"] is True

    def test_list_filter_is_active_false(self, client: TestClient, admin_headers, active_model_versions):
        r = client.get("/api/v1/admin/model-versions?is_active=false", headers=admin_headers)
        assert r.status_code == 200
        for item in r.json():
            assert item["is_active"] is False

    def test_list_filter_by_model_type(self, client: TestClient, admin_headers, active_model_versions):
        r = client.get("/api/v1/admin/model-versions?model_type=efficientnet_b0", headers=admin_headers)
        assert r.status_code == 200
        for item in r.json():
            assert item["model_type"] == "efficientnet_b0"

    def test_list_invalid_model_type_422(self, client: TestClient, admin_headers):
        r = client.get("/api/v1/admin/model-versions?model_type=unknown_arch", headers=admin_headers)
        assert r.status_code == 422

    def test_non_admin_user_forbidden(self, client: TestClient, user_headers, active_model_versions):
        r = client.get("/api/v1/admin/model-versions", headers=user_headers)
        assert r.status_code == 403

    def test_manager_forbidden(self, client: TestClient, manager_headers, active_model_versions):
        r = client.get("/api/v1/admin/model-versions", headers=manager_headers)
        assert r.status_code == 403

    def test_unauthenticated_forbidden(self, client: TestClient):
        r = client.get("/api/v1/admin/model-versions")
        assert r.status_code == 401


class TestGetModelVersion:
    def test_admin_can_get_existing(self, client: TestClient, admin_headers, active_model_versions):
        vid = active_model_versions[0].id
        r = client.get(f"/api/v1/admin/model-versions/{vid}", headers=admin_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == vid
        assert body["model_type"] == "efficientnet_b0"
        # Should have full detail fields
        assert "file_path" in body
        assert "sha256" in body

    def test_not_found_404(self, client: TestClient, admin_headers):
        r = client.get("/api/v1/admin/model-versions/999999", headers=admin_headers)
        assert r.status_code == 404

    def test_non_admin_forbidden(self, client: TestClient, user_headers, active_model_versions):
        vid = active_model_versions[0].id
        r = client.get(f"/api/v1/admin/model-versions/{vid}", headers=user_headers)
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------


class TestRegisterModelVersion:
    def test_relative_path_rejected_422(self, client: TestClient, admin_headers):
        """Relative path bị từ chối ngay ở service level."""
        r = client.post(
            "/api/v1/admin/model-versions",
            json={"manifest_path": "relative/path/manifest.json"},
            headers=admin_headers,
        )
        assert r.status_code == 422

    def test_nonexistent_absolute_path_422(self, client: TestClient, admin_headers):
        r = client.post(
            "/api/v1/admin/model-versions",
            json={"manifest_path": "C:/nonexistent_12345/manifest.json"},
            headers=admin_headers,
        )
        assert r.status_code == 422

    def test_non_admin_forbidden(self, client: TestClient, user_headers):
        r = client.post(
            "/api/v1/admin/model-versions",
            json={"manifest_path": "/some/path/manifest.json"},
            headers=user_headers,
        )
        assert r.status_code == 403

    def test_manager_forbidden(self, client: TestClient, manager_headers):
        r = client.post(
            "/api/v1/admin/model-versions",
            json={"manifest_path": "/some/path/manifest.json"},
            headers=manager_headers,
        )
        assert r.status_code == 403

    def test_missing_body_422(self, client: TestClient, admin_headers):
        r = client.post("/api/v1/admin/model-versions", json={}, headers=admin_headers)
        assert r.status_code == 422

    def test_accuracy_out_of_range_422(self, client: TestClient, admin_headers):
        r = client.post(
            "/api/v1/admin/model-versions",
            json={"manifest_path": "/x/manifest.json", "accuracy": 1.5},
            headers=admin_headers,
        )
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# Activate (idempotent + 404)
# ---------------------------------------------------------------------------


class TestActivateModelVersion:
    def test_activate_already_active_is_idempotent(
        self, client: TestClient, admin_headers, active_model_versions
    ):
        """Version đang active → idempotent 200, không deactivate gì."""
        vid = active_model_versions[0].id
        r = client.post(f"/api/v1/admin/model-versions/{vid}/activate", headers=admin_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["is_active"] is True
        assert body["deactivated_version_id"] is None

    def test_not_found_404(self, client: TestClient, admin_headers):
        r = client.post("/api/v1/admin/model-versions/999999/activate", headers=admin_headers)
        assert r.status_code == 404

    def test_non_admin_forbidden(self, client: TestClient, user_headers, active_model_versions):
        vid = active_model_versions[0].id
        r = client.post(f"/api/v1/admin/model-versions/{vid}/activate", headers=user_headers)
        assert r.status_code == 403

    def test_manager_forbidden(self, client: TestClient, manager_headers, active_model_versions):
        vid = active_model_versions[0].id
        r = client.post(f"/api/v1/admin/model-versions/{vid}/activate", headers=manager_headers)
        assert r.status_code == 403
