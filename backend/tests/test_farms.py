"""Kiểm thử CRUD Farm và phạm vi sở hữu của Tuần 2."""

from app.models import Farm, Scan


FARM_PAYLOAD = {
    "name": "Trang trại Đà Lạt",
    "location_text": "Lâm Đồng",
}


def test_user_cannot_manage_farms(client, user_headers):
    response = client.post(
        "/api/v1/farms", json=FARM_PAYLOAD, headers=user_headers
    )
    assert response.status_code == 403


def test_manager_full_crud_on_owned_farm(
    client, db_session, manager_headers, manager_user
):
    created = client.post(
        "/api/v1/farms", json=FARM_PAYLOAD, headers=manager_headers
    )
    assert created.status_code == 201
    farm = created.json()
    assert farm["owner_id"] == manager_user.id

    listed = client.get("/api/v1/farms", headers=manager_headers)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [farm["id"]]

    detail = client.get(
        f"/api/v1/farms/{farm['id']}", headers=manager_headers
    )
    assert detail.status_code == 200
    assert detail.json()["id"] == farm["id"]
    assert detail.json()["owner_id"] == manager_user.id

    updated = client.put(
        f"/api/v1/farms/{farm['id']}",
        json={"name": "Trang trại Đà Lạt - cập nhật"},
        headers=manager_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["name"].endswith("cập nhật")

    scan = Scan(
        user_id=manager_user.id,
        farm_id=farm["id"],
        image_path="storage/uploads/farm-history.jpg",
        confidence=0.8,
    )
    db_session.add(scan)
    db_session.commit()
    scan_id = scan.id

    deleted = client.delete(
        f"/api/v1/farms/{farm['id']}", headers=manager_headers
    )
    assert deleted.status_code == 204
    assert client.get("/api/v1/farms", headers=manager_headers).json() == []
    assert client.get(
        f"/api/v1/farms/{farm['id']}", headers=manager_headers
    ).status_code == 404

    archived_farm = db_session.get(Farm, farm["id"])
    assert archived_farm is not None
    assert archived_farm.archived_at is not None
    db_session.expire_all()
    assert db_session.get(Scan, scan_id).farm_id == farm["id"]


def test_manager_cannot_access_another_managers_farm(
    client,
    manager_headers,
    other_manager_user,
    token_headers,
):
    other_headers = token_headers(other_manager_user)
    farm = client.post(
        "/api/v1/farms", json=FARM_PAYLOAD, headers=manager_headers
    ).json()

    assert client.get("/api/v1/farms", headers=other_headers).json() == []
    assert client.get(
        f"/api/v1/farms/{farm['id']}", headers=other_headers
    ).status_code == 403
    assert (
        client.put(
            f"/api/v1/farms/{farm['id']}",
            json={"name": "Chiếm quyền"},
            headers=other_headers,
        ).status_code
        == 403
    )
    assert (
        client.delete(f"/api/v1/farms/{farm['id']}", headers=other_headers)
        .status_code
        == 403
    )


def test_admin_cannot_use_manager_farm_endpoints(
    client,
    manager_headers,
    admin_headers,
):
    farm = client.post(
        "/api/v1/farms", json=FARM_PAYLOAD, headers=manager_headers
    ).json()

    assert client.post(
        "/api/v1/farms", json=FARM_PAYLOAD, headers=admin_headers
    ).status_code == 403
    assert client.get(
        "/api/v1/farms", headers=admin_headers
    ).status_code == 403
    assert client.get(
        f"/api/v1/farms/{farm['id']}", headers=admin_headers
    ).status_code == 403
    assert client.put(
        f"/api/v1/farms/{farm['id']}",
        json={"name": "Admin không được sửa"},
        headers=admin_headers,
    ).status_code == 403
    assert client.delete(
        f"/api/v1/farms/{farm['id']}", headers=admin_headers
    ).status_code == 403

    owned_farms = client.get("/api/v1/farms", headers=manager_headers).json()
    assert len(owned_farms) == 1
    assert owned_farms[0]["name"] == FARM_PAYLOAD["name"]


def test_farm_name_cannot_be_blank(client, manager_headers):
    response = client.post(
        "/api/v1/farms",
        json={"name": "   ", "location_text": "Huế"},
        headers=manager_headers,
    )
    assert response.status_code == 422


def test_manager_can_clear_optional_farm_location(client, manager_headers):
    created = client.post(
        "/api/v1/farms", json=FARM_PAYLOAD, headers=manager_headers
    ).json()

    response = client.put(
        f"/api/v1/farms/{created['id']}",
        json={"location_text": None},
        headers=manager_headers,
    )

    assert response.status_code == 200
    assert response.json()["location_text"] is None
