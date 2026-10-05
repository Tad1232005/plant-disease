"""Kiểm thử Admin/Manager cấp và liệt kê tài khoản Tuần 4."""

import pytest

from app.models import User


def user_payload(username: str) -> dict[str, str]:
    return {
        "username": username,
        "email": f"{username}@example.com",
        "password": "StrongPass123!",
        "full_name": f"Test {username}",
    }


@pytest.mark.parametrize("role", ["technician", "manager"])
def test_admin_can_create_supported_roles(client, admin_headers, role):
    response = client.post(
        "/api/v1/admin/users",
        json={**user_payload(f"admin_created_{role}"), "role": role},
        headers=admin_headers,
    )

    assert response.status_code == 201
    assert response.json()["role"] == role
    assert response.json()["created_by"] is not None


@pytest.mark.parametrize("role", ["user", "admin", "owner"])
def test_admin_cannot_create_unsupported_role(client, admin_headers, role):
    response = client.post(
        "/api/v1/admin/users",
        json={**user_payload(f"invalid_{role}"), "role": role},
        headers=admin_headers,
    )

    assert response.status_code == 422


def test_admin_can_filter_users_by_role(client, admin_headers):
    client.post(
        "/api/v1/admin/users",
        json={**user_payload("listed_technician"), "role": "technician"},
        headers=admin_headers,
    )
    client.post(
        "/api/v1/admin/users",
        json={**user_payload("listed_manager"), "role": "manager"},
        headers=admin_headers,
    )

    response = client.get(
        "/api/v1/admin/users?role=technician",
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert {item["username"] for item in response.json()} == {
        "listed_technician"
    }


def test_manager_creates_user_with_hardcoded_role(
    client,
    manager_headers,
    manager_user,
):
    response = client.post(
        "/api/v1/manager/users",
        json=user_payload("managed_farmer"),
        headers=manager_headers,
    )

    assert response.status_code == 201
    assert response.json()["role"] == "user"
    assert response.json()["created_by"] == manager_user.id


def test_manager_cannot_create_admin(
    client,
    manager_headers,
    db_session,
):
    """Regression bảo mật chính: field role không được Manager truyền vào."""
    response = client.post(
        "/api/v1/manager/users",
        json={**user_payload("privilege_escalation"), "role": "admin"},
        headers=manager_headers,
    )

    assert response.status_code == 422
    assert db_session.query(User).filter_by(
        username="privilege_escalation"
    ).first() is None


def test_manager_lists_only_users_created_by_self(
    client,
    manager_headers,
    other_manager_user,
    token_headers,
):
    other_headers = token_headers(other_manager_user)
    client.post(
        "/api/v1/manager/users",
        json=user_payload("first_managers_user"),
        headers=manager_headers,
    )
    client.post(
        "/api/v1/manager/users",
        json=user_payload("other_managers_user"),
        headers=other_headers,
    )

    response = client.get("/api/v1/manager/users", headers=manager_headers)

    assert response.status_code == 200
    assert [item["username"] for item in response.json()] == [
        "first_managers_user"
    ]


def test_role_boundaries_for_user_management(
    client,
    user_headers,
    manager_headers,
    admin_headers,
):
    assert client.get(
        "/api/v1/admin/users", headers=manager_headers
    ).status_code == 403
    assert client.get(
        "/api/v1/manager/users", headers=admin_headers
    ).status_code == 403
    assert client.get(
        "/api/v1/manager/users", headers=user_headers
    ).status_code == 403

def test_manager_can_suspend_and_activate_own_user(client, manager_headers):
    created = client.post(
        "/api/v1/manager/users",
        json=user_payload("user_to_suspend"),
        headers=manager_headers,
    ).json()
    user_id = created["id"]

    # Suspend
    res = client.patch(
        f"/api/v1/manager/users/{user_id}/status",
        json={"status": "suspended", "reason": "Tạm đình chỉ vụ mùa"},
        headers=manager_headers,
    )
    assert res.status_code == 200
    assert res.json()["status"] == "suspended"

    # Activate lại
    res2 = client.patch(
        f"/api/v1/manager/users/{user_id}/status",
        json={"status": "active", "reason": "Bắt đầu vụ mùa mới"},
        headers=manager_headers,
    )
    assert res2.status_code == 200
    assert res2.json()["status"] == "active"


def test_manager_can_reset_password_for_own_user(client, manager_headers):
    created = client.post(
        "/api/v1/manager/users",
        json=user_payload("user_to_reset_pw"),
        headers=manager_headers,
    ).json()
    user_id = created["id"]

    res = client.post(
        f"/api/v1/manager/users/{user_id}/reset-password",
        json={"new_password": "NewSecretPass456!"},
        headers=manager_headers,
    )
    assert res.status_code == 200

    # Đăng nhập bằng mật khẩu mới
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": "user_to_reset_pw", "password": "NewSecretPass456!"},
    )
    assert login_res.status_code == 200


def test_manager_cannot_manage_other_managers_user(client, manager_headers, other_manager_user, token_headers):
    other_headers = token_headers(other_manager_user)
    created = client.post(
        "/api/v1/manager/users",
        json=user_payload("other_manager_sub_user"),
        headers=other_headers,
    ).json()
    other_user_id = created["id"]

    # Manager 1 cố gắng suspend user của Manager 2 -> 403 Forbidden
    res = client.patch(
        f"/api/v1/manager/users/{other_user_id}/status",
        json={"status": "suspended", "reason": "Hack status"},
        headers=manager_headers,
    )
    assert res.status_code == 403

    # Manager 1 cố gắng reset pass user của Manager 2 -> 403 Forbidden
    res_pw = client.post(
        f"/api/v1/manager/users/{other_user_id}/reset-password",
        json={"new_password": "HackPassword123!"},
        headers=manager_headers,
    )
    assert res_pw.status_code == 403

