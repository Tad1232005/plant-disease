"""Test Admin và Manager user detail endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestAdminGetUserDetail:
    def test_admin_can_get_any_user(
        self, client: TestClient, admin_headers, normal_user, manager_user
    ):
        """Admin lấy chi tiết user bất kỳ theo id."""
        r = client.get(f"/api/v1/admin/users/{normal_user.id}", headers=admin_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == normal_user.id
        assert body["username"] == normal_user.username
        assert body["role"] == "user"

    def test_admin_can_get_manager(self, client: TestClient, admin_headers, manager_user):
        r = client.get(f"/api/v1/admin/users/{manager_user.id}", headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["role"] == "manager"

    def test_not_found_returns_404(self, client: TestClient, admin_headers):
        r = client.get("/api/v1/admin/users/999999", headers=admin_headers)
        assert r.status_code == 404

    def test_manager_cannot_use_admin_endpoint(
        self, client: TestClient, manager_headers, normal_user
    ):
        r = client.get(f"/api/v1/admin/users/{normal_user.id}", headers=manager_headers)
        assert r.status_code == 403

    def test_user_cannot_use_admin_endpoint(
        self, client: TestClient, user_headers, admin_user
    ):
        r = client.get(f"/api/v1/admin/users/{admin_user.id}", headers=user_headers)
        assert r.status_code == 403

    def test_unauthenticated_returns_401(self, client: TestClient, normal_user):
        r = client.get(f"/api/v1/admin/users/{normal_user.id}")
        assert r.status_code == 401


class TestAdminSuspendActivateUser:
    def test_admin_can_suspend_user(
        self, client: TestClient, admin_headers, admin_user, user_factory, db_session
    ):
        """Admin suspend một User thường."""
        target = user_factory("suspendable_user", role="user", created_by=admin_user.id)
        r = client.patch(
            f"/api/v1/admin/users/{target.id}/status",
            json={"status": "suspended", "reason": "Vi phạm điều khoản"},
            headers=admin_headers,
        )
        assert r.status_code == 200
        assert r.json()["status"] == "suspended"

    def test_admin_can_reactivate_user(
        self, client: TestClient, admin_headers, admin_user, user_factory, db_session
    ):
        """Admin activate lại user đã suspend."""
        target = user_factory("reactive_user", role="user", created_by=admin_user.id)
        # Suspend
        client.patch(
            f"/api/v1/admin/users/{target.id}/status",
            json={"status": "suspended", "reason": "Test suspend"},
            headers=admin_headers,
        )
        # Reactivate
        r = client.patch(
            f"/api/v1/admin/users/{target.id}/status",
            json={"status": "active", "reason": "Khôi phục"},
            headers=admin_headers,
        )
        assert r.status_code == 200
        assert r.json()["status"] == "active"

    def test_suspend_without_reason_422(
        self, client: TestClient, admin_headers, normal_user
    ):
        r = client.patch(
            f"/api/v1/admin/users/{normal_user.id}/status",
            json={"status": "suspended"},
            headers=admin_headers,
        )
        assert r.status_code == 422

    def test_manager_cannot_suspend(
        self, client: TestClient, manager_headers, normal_user
    ):
        r = client.patch(
            f"/api/v1/admin/users/{normal_user.id}/status",
            json={"status": "suspended", "reason": "Unauthorized attempt"},
            headers=manager_headers,
        )
        assert r.status_code == 403


class TestManagerGetUserDetail:
    def test_manager_can_get_own_created_user(
        self, client: TestClient, manager_headers, manager_user, user_factory
    ):
        """Manager lấy chi tiết user do mình tạo."""
        managed = user_factory(
            "my_managed_user", role="user", created_by=manager_user.id
        )
        r = client.get(f"/api/v1/manager/users/{managed.id}", headers=manager_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == managed.id
        assert body["created_by"] == manager_user.id

    def test_manager_cannot_get_other_manager_user(
        self,
        client: TestClient,
        manager_headers,
        other_manager_user,
        user_factory,
    ):
        """Manager không thể xem user do manager khác tạo."""
        other_managed = user_factory(
            "other_managed_user", role="user", created_by=other_manager_user.id
        )
        r = client.get(
            f"/api/v1/manager/users/{other_managed.id}", headers=manager_headers
        )
        assert r.status_code == 404

    def test_manager_not_found_404(self, client: TestClient, manager_headers):
        r = client.get("/api/v1/manager/users/999999", headers=manager_headers)
        assert r.status_code == 404

    def test_user_cannot_use_manager_endpoint(
        self, client: TestClient, user_headers, normal_user
    ):
        r = client.get(f"/api/v1/manager/users/{normal_user.id}", headers=user_headers)
        assert r.status_code == 403
