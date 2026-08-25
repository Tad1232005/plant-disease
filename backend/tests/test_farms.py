"""Kiểm thử CRUD Farm và phạm vi sở hữu của Tuần 2."""


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
    client, manager_headers, manager_user
):
    created = client.post(
        "/api/v1/farms", json=FARM_PAYLOAD, headers=manager_headers
    )
    assert created.status_code == 201
    farm = created.json()
    assert farm["owner_id"] == manager_user.id

    detail = client.get(
        f"/api/v1/farms/{farm['id']}", headers=manager_headers
    )
    assert detail.status_code == 200

    updated = client.put(
        f"/api/v1/farms/{farm['id']}",
        json={"name": "Trang trại Đà Lạt - cập nhật"},
        headers=manager_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["name"].endswith("cập nhật")

    deleted = client.delete(
        f"/api/v1/farms/{farm['id']}", headers=manager_headers
    )
    assert deleted.status_code == 204
    assert (
        client.get(f"/api/v1/farms/{farm['id']}", headers=manager_headers)
        .status_code
        == 404
    )


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

    assert (
        client.get(f"/api/v1/farms/{farm['id']}", headers=other_headers)
        .status_code
        == 403
    )
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


def test_admin_lists_all_farms_while_manager_only_lists_owned(
    client,
    manager_headers,
    other_manager_user,
    token_headers,
    admin_headers,
):
    other_headers = token_headers(other_manager_user)
    client.post("/api/v1/farms", json=FARM_PAYLOAD, headers=manager_headers)
    client.post(
        "/api/v1/farms",
        json={"name": "Farm miền Tây", "location_text": "Cần Thơ"},
        headers=other_headers,
    )

    assert len(
        client.get("/api/v1/farms", headers=manager_headers).json()) == 1
    assert len(client.get("/api/v1/farms", headers=admin_headers).json()) == 2


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
