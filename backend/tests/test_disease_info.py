"""Kiểm thử Public Read và Admin RBAC cho DiseaseInfo APIs theo đúng Schema."""


def test_get_disease_list_public(client):
    """Khách không cần token vẫn xem được danh sách bệnh."""
    response = client.get("/api/v1/disease-info")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_disease_admin_success(client, admin_headers):
    """Admin có quyền thêm thông tin bệnh mới."""
    payload = {
        "label_key": "apple_scab",
        "disease_name": "Bệnh sẹo táo",
        "description": "Vết bệnh màu đen đốm xuất hiện trên lá",
        "treatment": "Phun thuốc gốc đồng định kỳ",
        "severity_level": "medium"
    }
    response = client.post("/api/v1/disease-info",
                           json=payload, headers=admin_headers)
    assert response.status_code == 201
    assert response.json()["label_key"] == "apple_scab"
    assert response.json()["disease_name"] == "Bệnh sẹo táo"


def test_create_disease_normal_user_forbidden(client, user_headers):
    """User thường tạo thông tin bệnh bị chặn 403 Forbidden."""
    payload = {
        "label_key": "corn_blight",
        "disease_name": "Cháy lá ngô",
        "description": "Vết đốm nâu",
        "treatment": "Cắt tỉa lá bệnh",
        "severity_level": "high"
    }
    response = client.post("/api/v1/disease-info",
                           json=payload, headers=user_headers)
    assert response.status_code == 403
