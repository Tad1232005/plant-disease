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
