"""Kiểm thử CRUD Disease Info public/admin của Tuần 2."""


DISEASE_PAYLOAD = {
    "label_key": "Tomato___Early_blight",
    "disease_name": "Bệnh cháy lá sớm cà chua",
    "description": "Đốm nâu đồng tâm trên lá già.",
    "treatment": "Loại bỏ lá bệnh và luân canh.",
    "severity_level": "medium",
}


def test_public_can_list_and_get_disease(client, admin_headers):
    created = client.post(
        "/api/v1/disease-info", json=DISEASE_PAYLOAD, headers=admin_headers
    )
    assert created.status_code == 201

    listed = client.get("/api/v1/disease-info")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    detail = client.get(
        f"/api/v1/disease-info/{DISEASE_PAYLOAD['label_key']}"
    )
    assert detail.status_code == 200
    assert detail.json()["disease_name"] == DISEASE_PAYLOAD["disease_name"]


def test_admin_full_crud_disease_info(client, admin_headers):
    created = client.post(
        "/api/v1/disease-info", json=DISEASE_PAYLOAD, headers=admin_headers
    )
    assert created.status_code == 201
    assert "created_at" in created.json()

    duplicate = client.post(
        "/api/v1/disease-info", json=DISEASE_PAYLOAD, headers=admin_headers
    )
    assert duplicate.status_code == 400

    updated = client.put(
        f"/api/v1/disease-info/{DISEASE_PAYLOAD['label_key']}",
        json={"severity_level": "high", "treatment": "Xử lý mới"},
        headers=admin_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["severity_level"] == "high"

    deleted = client.delete(
        f"/api/v1/disease-info/{DISEASE_PAYLOAD['label_key']}",
        headers=admin_headers,
    )
    assert deleted.status_code == 204
    assert (
        client.get(
            f"/api/v1/disease-info/{DISEASE_PAYLOAD['label_key']}"
        ).status_code
        == 404
    )


def test_non_admin_cannot_write_disease_info(
    client, user_headers, technician_headers
):
    assert (
        client.post(
            "/api/v1/disease-info",
            json=DISEASE_PAYLOAD,
            headers=user_headers,
        ).status_code
        == 403
    )
    # Regression quan trọng: Technician chỉ được đề xuất, không sửa trực tiếp.
    assert (
        client.put(
            f"/api/v1/disease-info/{DISEASE_PAYLOAD['label_key']}",
            json={"severity_level": "high"},
            headers=technician_headers,
        ).status_code
        == 403
    )


def test_invalid_severity_is_rejected(client, admin_headers):
    response = client.post(
        "/api/v1/disease-info",
        json={**DISEASE_PAYLOAD, "severity_level": "critical"},
        headers=admin_headers,
    )
    assert response.status_code == 422
