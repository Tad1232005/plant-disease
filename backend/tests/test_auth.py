"""Module kiểm thử tích hợp cho Auth API."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_register_user():
    """Test API đăng ký tài khoản mới thành công."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "test_user_pytest",
            "email": "pytest@example.com",
            "password": "strongpassword123",
            "full_name": "Pytest User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "test_user_pytest"
    assert "id" in data


def test_login_user():
    """Test API đăng nhập và nhận Token."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "test_user_pytest", "password": "strongpassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert response.cookies.get("refresh_token") is not None
