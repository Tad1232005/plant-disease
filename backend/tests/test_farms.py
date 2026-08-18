"""Kiểm thử CRUD và Phân quyền sở hữu Trang trại (Farm APIs) theo đúng Schema."""

# pylint: disable=unexpected-keyword-arg,no-value-for-parameter,redefined-outer-name
# flake8: noqa: E402

def test_create_farm_manager_success(client, manager_headers):
    """Manager tạo trang trại thành công."""
    headers, _ = manager_headers
    payload = {
        "name": "Trang trại Đà Lạt 1",
        "location_text": "Số 12 Phường 3, Đà Lạt, Lâm Đồng"
    }
    response = client.post("/api/v1/farms", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.json()["name"] == "Trang trại Đà Lạt 1"
    assert response.json()["location_text"] == "Số 12 Phường 3, Đà Lạt, Lâm Đồng"


def test_create_farm_user_forbidden(client, user_headers):
    """User thường không có quyền tạo trang trại (chỉ Manager/Admin)."""
    payload = {
        "name": "Trang trại Cần Thơ",
        "location_text": "Cần Thơ"
    }
    response = client.post("/api/v1/farms", json=payload, headers=user_headers)
    assert response.status_code == 403
