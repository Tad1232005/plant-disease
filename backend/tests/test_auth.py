"""Module kiểm thử tích hợp cho Auth API."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_register_user(client):
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


def test_login_user(client):
    """Test API đăng nhập."""
    # Đăng ký trước 1 user để test đăng nhập
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "login_user",
            "email": "login@example.com",
            "password": "strongpassword123",
            "full_name": "Login Test User",
        },
    )

    # Tiến hành test đăng nhập
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "login_user", "password": "strongpassword123"},
    )
    assert response.status_code == 200
