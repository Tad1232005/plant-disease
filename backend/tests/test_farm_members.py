"""Kiểm thử deliverable Managed User -> Farm Member Tuần 4."""

import io

from PIL import Image

from app.core.config import settings
from app.models import FarmMember, Scan, User
from app.services.predict_service import predict_service


def create_payload(username: str, role: str | None = None) -> dict[str, str]:
    payload = {
        "username": username,
        "email": f"{username}@example.com",
        "password": "StrongPass123!",
        "full_name": f"Test {username}",
    }
    if role is not None:
        payload["role"] = role
    return payload


def login_headers(client, username: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "StrongPass123!"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_week4_deliverable_flow(
    client,
    admin_headers,
    db_session,
    monkeypatch,
    tmp_path,
    active_model_versions,
):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(
        predict_service,
        "predict",
        lambda _data, specs, mode: {
            "label": "Tomato___Early_blight",
            "candidate_label": "Tomato___Early_blight",
            "confidence": 0.8,
            "is_valid_leaf": True,
            "top_k": [
                {
                    "label": "Tomato___Early_blight",
                    "confidence": 0.8,
                    "rank": 1,
                },
                {
                    "label": "Tomato___Late_blight",
                    "confidence": 0.15,
                    "rank": 2,
                },
                {
                    "label": "Tomato___healthy",
                    "confidence": 0.05,
                    "rank": 3,
                },
            ],
            "model_version": specs[0].version_name,
            "primary_model_version_id": specs[0].id,
            "inference_mode": mode,
            "validation_status": "accepted",
            "rejection_reason": None,
            "agreement_status": "agreed",
            "agreement_count": len(specs),
            "models_requested": len(specs),
            "models_succeeded": len(specs),
            "top1_top2_margin": 0.65,
            "ensemble_entropy": 0.2,
            "js_divergence": 0.0,
            "energy_score": -3.0,
            "ood_score": 0.2,
            "policy_version": "ensemble-baseline-v1",
            "model_results": [
                {
                    "model_version_id": spec.id,
                    "version_name": spec.version_name,
                    "model_type": spec.model_type,
                    "execution_order": index,
                    "predicted_label": "Tomato___Early_blight",
                    "confidence": 0.8,
                    "top1_top2_margin": 0.65,
                    "entropy": 0.2,
                    "energy_score": -3.0,
                    "accepted": True,
                    "latency_ms": 10.0,
                    "error_code": None,
                    "top_k": [
                        {
                            "label": "Tomato___Early_blight",
                            "confidence": 0.8,
                            "rank": 1,
                        }
                    ],
                }
                for index, spec in enumerate(specs, start=1)
            ],
        },
    )
    manager_response = client.post(
        "/api/v1/admin/users",
        json=create_payload("week4_manager", role="manager"),
        headers=admin_headers,
    )
    assert manager_response.status_code == 201
    manager_headers = login_headers(client, "week4_manager")

    managed_users = []
    for username in ("managed_user_1", "managed_user_2"):
        response = client.post(
            "/api/v1/manager/users",
            json=create_payload(username),
            headers=manager_headers,
        )
        assert response.status_code == 201
        managed_users.append(response.json())

    farm = client.post(
        "/api/v1/farms",
        json={"name": "Farm Tuần 4", "location_text": "Lâm Đồng"},
        headers=manager_headers,
    ).json()

    for user in managed_users:
        response = client.post(
            f"/api/v1/farms/{farm['id']}/members",
            json={"user_id": user["id"]},
            headers=manager_headers,
        )
        assert response.status_code == 201
        assert response.json()["user"]["username"] == user["username"]
        assert response.json()["added_by"] == manager_response.json()["id"]

    listed = client.get(
        f"/api/v1/farms/{farm['id']}/members",
        headers=manager_headers,
    )
    assert listed.status_code == 200
    assert {item["user"]["username"] for item in listed.json()} == {
        "managed_user_1",
        "managed_user_2",
    }
    assert db_session.query(FarmMember).count() == 2

    for user in managed_users:
        user_headers = login_headers(client, user["username"])
        image = io.BytesIO()
        Image.new("RGB", (64, 64), color="green").save(image, "JPEG")
        image.seek(0)
        predicted = client.post(
            "/api/v1/predict",
            files={"file": (f"{user['username']}.jpg", image, "image/jpeg")},
            data={"farm_id": str(farm["id"])},
            headers=user_headers,
        )
        assert predicted.status_code == 200
        assert predicted.json()["farm_assignment_status"] == "assigned"
        assert predicted.json()["farm_id"] == farm["id"]

    assert db_session.query(Scan).filter_by(farm_id=farm["id"]).count() == 2


def test_manager_cannot_assign_another_managers_user(
    client,
    manager_headers,
    other_manager_user,
    token_headers,
):
    other_headers = token_headers(other_manager_user)
    foreign_user = client.post(
        "/api/v1/manager/users",
        json=create_payload("foreign_managed_user"),
        headers=other_headers,
    ).json()
    farm = client.post(
        "/api/v1/farms",
        json={"name": "Owned Farm"},
        headers=manager_headers,
    ).json()

    response = client.post(
        f"/api/v1/farms/{farm['id']}/members",
        json={"user_id": foreign_user["id"]},
        headers=manager_headers,
    )

    assert response.status_code == 403


def test_manager_cannot_manage_members_of_another_farm(
    client,
    manager_headers,
    other_manager_user,
    token_headers,
):
    other_headers = token_headers(other_manager_user)
    farm = client.post(
        "/api/v1/farms",
        json={"name": "Foreign Farm"},
        headers=other_headers,
    ).json()

    assert client.get(
        f"/api/v1/farms/{farm['id']}/members",
        headers=manager_headers,
    ).status_code == 403


def test_duplicate_member_is_rejected_and_delete_keeps_user(
    client,
    manager_headers,
    db_session,
):
    user = client.post(
        "/api/v1/manager/users",
        json=create_payload("member_to_remove"),
        headers=manager_headers,
    ).json()
    farm = client.post(
        "/api/v1/farms",
        json={"name": "Membership Farm"},
        headers=manager_headers,
    ).json()
    url = f"/api/v1/farms/{farm['id']}/members"

    assert client.post(
        url,
        json={"user_id": user["id"], "added_by": 999_999},
        headers=manager_headers,
    ).status_code == 422
    assert client.post(
        url, json={"user_id": user["id"]}, headers=manager_headers
    ).status_code == 201
    assert client.post(
        url, json={"user_id": user["id"]}, headers=manager_headers
    ).status_code == 409

    deleted = client.delete(
        f"{url}/{user['id']}",
        headers=manager_headers,
    )
    assert deleted.status_code == 204
    assert client.get(url, headers=manager_headers).json() == []
    assert db_session.get(User, user["id"]) is not None
