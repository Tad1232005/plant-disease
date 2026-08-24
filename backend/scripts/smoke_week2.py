"""Test API Tuần 1-2.

Ví dụ:
    python scripts/smoke_week2.py
    python scripts/smoke_week2.py --base-url http://localhost:8000/api/v1
"""

import argparse
import sys
from uuid import uuid4

import httpx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def require(response: httpx.Response, expected: int, name: str) -> dict:
    if response.status_code != expected:
        print(
            f"[FAIL] {name}: expected {expected}, got {response.status_code} "
            f"- {response.text}"
        )
        raise SystemExit(1)
    print(f"[PASS] {name}: HTTP {response.status_code}")
    return response.json() if response.content else {}


def login(client: httpx.Client, base_url: str, username: str, password: str):
    body = require(
        client.post(
            f"{base_url}/auth/login",
            json={"username": username, "password": password},
        ),
        200,
        f"login {username}",
    )
    return {"Authorization": f"Bearer {body['access_token']}"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base-url", default="http://127.0.0.1:8000/api/v1"
    )
    parser.add_argument("--demo-password", default="123321")
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")
    suffix = uuid4().hex[:8]

    with httpx.Client(timeout=10) as client:
        register_body = {
            "username": f"smoke_{suffix}",
            "email": f"smoke_{suffix}@example.com",
            "password": "123321",
            "full_name": "Smoke Test User",
        }
        require(
            client.post(f"{base_url}/auth/register", json=register_body),
            201,
            "auth/register",
        )
        user_headers = login(
            client,
            base_url,
            register_body["username"],
            register_body["password"],
        )
        require(
            client.get(f"{base_url}/auth/me", headers=user_headers),
            200,
            "auth/me",
        )
        require(
            client.post(f"{base_url}/auth/refresh"),
            200,
            "auth/refresh",
        )
        require(
            client.post(f"{base_url}/auth/logout", headers=user_headers),
            204,
            "auth/logout",
        )

    with httpx.Client(timeout=10) as manager_client:
        manager_headers = login(
            manager_client,
            base_url,
            "manager_user",
            args.demo_password,
        )
        farm = require(
            manager_client.post(
                f"{base_url}/farms",
                json={
                    "name": f"Smoke Farm {suffix}",
                    "location_text": "Đà Lạt",
                },
                headers=manager_headers,
            ),
            201,
            "farms/create",
        )
        require(
            manager_client.get(
                f"{base_url}/farms/{farm['id']}", headers=manager_headers
            ),
            200,
            "farms/get",
        )
        require(
            manager_client.put(
                f"{base_url}/farms/{farm['id']}",
                json={"location_text": "Lâm Đồng"},
                headers=manager_headers,
            ),
            200,
            "farms/update",
        )
        require(
            manager_client.delete(
                f"{base_url}/farms/{farm['id']}", headers=manager_headers
            ),
            204,
            "farms/delete",
        )

    with httpx.Client(timeout=10) as admin_client:
        admin_headers = login(
            admin_client,
            base_url,
            "admin_user",
            args.demo_password,
        )
        disease = {
            "label_key": f"Smoke___Disease_{suffix}",
            "disease_name": "Bệnh kiểm thử",
            "description": "Dữ liệu chỉ dùng cho smoke test.",
            "treatment": "Không áp dụng.",
            "severity_level": "low",
        }
        require(
            admin_client.post(
                f"{base_url}/disease-info",
                json=disease,
                headers=admin_headers,
            ),
            201,
            "disease-info/create",
        )
        require(
            admin_client.get(
                f"{base_url}/disease-info/{disease['label_key']}"
            ),
            200,
            "disease-info/get public",
        )
        require(
            admin_client.put(
                f"{base_url}/disease-info/{disease['label_key']}",
                json={"severity_level": "medium"},
                headers=admin_headers,
            ),
            200,
            "disease-info/update",
        )
        require(
            admin_client.delete(
                f"{base_url}/disease-info/{disease['label_key']}",
                headers=admin_headers,
            ),
            204,
            "disease-info/delete",
        )

    print("\nAll Week 1-2 smoke tests passed.")


if __name__ == "__main__":
    try:
        main()
    except httpx.ConnectError:
        print("Cannot connect to the server. Start uvicorn first.")
        sys.exit(1)
