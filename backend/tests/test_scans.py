"""Kiểm thử Scan API theo ownership Tuần 4."""

from app.core.config import settings
import json

from app.models import DiseaseInfo, ModelVersion, Scan, ScanModelResult, ScanTopK


def create_scan(db_session, user_id: int, suffix: str) -> Scan:
    model = db_session.query(ModelVersion).filter_by(
        version_name="scan-test-v1"
    ).first()
    if model is None:
        model = ModelVersion(
            version_name="scan-test-v1",
            model_type="efficientnet_b0",
            file_path="models/scan-test.pt",
            is_active=False,
        )
        db_session.add(model)
        db_session.flush()
    scan = Scan(
        user_id=user_id,
        image_path=f"storage/uploads/{suffix}.jpg",
        predicted_label="Tomato___Early_blight",
        confidence=0.8,
        is_valid_leaf=True,
        model_version="v1-demo",
        primary_model_version_id=model.id,
        inference_mode="basic",
    )
    db_session.add(scan)
    db_session.flush()
    db_session.add_all(
        [
            ScanTopK(
                scan_id=scan.id,
                label="Tomato___Late_blight",
                confidence=0.1,
                rank=2,
            ),
            ScanTopK(
                scan_id=scan.id,
                label="Tomato___Early_blight",
                confidence=0.8,
                rank=1,
            ),
        ]
    )
    db_session.add(
        ScanModelResult(
            scan_id=scan.id,
            model_version_id=model.id,
            execution_order=1,
            predicted_label="Tomato___Early_blight",
            confidence=0.8,
            accepted=True,
            topk_json=json.dumps(
                [{"label": "Tomato___Early_blight", "confidence": 0.8, "rank": 1}]
            ),
        )
    )
    db_session.commit()
    db_session.refresh(scan)
    return scan


def test_scan_history_contains_only_current_users_scans(
    client,
    db_session,
    normal_user,
    technician_user,
    user_headers,
):
    own_scan = create_scan(db_session, normal_user.id, "own")
    create_scan(db_session, technician_user.id, "foreign")

    response = client.get("/api/v1/scans/history", headers=user_headers)

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [own_scan.id]
    assert client.get("/api/v1/scans/history").status_code == 401


def test_scan_history_has_bounded_pagination(
    client,
    db_session,
    normal_user,
    user_headers,
):
    scans = [
        create_scan(db_session, normal_user.id, f"page-{index}")
        for index in range(3)
    ]

    response = client.get(
        "/api/v1/scans/history?limit=1&offset=1",
        headers=user_headers,
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [scans[1].id]
    assert client.get(
        "/api/v1/scans/history?limit=101",
        headers=user_headers,
    ).status_code == 422


def test_scan_detail_includes_disease_and_sorted_top3(
    client,
    db_session,
    normal_user,
    user_headers,
):
    db_session.add(
        DiseaseInfo(
            label_key="Tomato___Early_blight",
            disease_name="Bệnh cháy lá sớm",
            treatment="Loại bỏ lá bệnh",
            severity_level="medium",
            is_active=False,
        )
    )
    db_session.commit()
    scan = create_scan(db_session, normal_user.id, "detail")

    response = client.get(
        f"/api/v1/scans/{scan.id}",
        headers=user_headers,
    )

    assert response.status_code == 200
    assert response.json()["disease_name"] == "Bệnh cháy lá sớm"
    assert response.json()["treatment"] == "Loại bỏ lá bệnh"
    assert [item["rank"] for item in response.json()["top3"]] == [1, 2]
    assert response.json()["model_results"][0]["model_type"] == "efficientnet_b0"


def test_other_user_and_admin_cannot_access_users_scan(
    client,
    db_session,
    normal_user,
    technician_headers,
    admin_headers,
):
    scan = create_scan(db_session, normal_user.id, "private")

    assert client.get(
        f"/api/v1/scans/{scan.id}", headers=technician_headers
    ).status_code == 403
    assert client.delete(
        f"/api/v1/scans/{scan.id}", headers=admin_headers
    ).status_code == 403
    assert client.get(
        "/api/v1/scans/history", headers=admin_headers
    ).json() == []


def test_owner_can_delete_scan_and_topk_cascades(
    client,
    db_session,
    normal_user,
    user_headers,
    tmp_path,
    monkeypatch,
):
    scan = create_scan(db_session, normal_user.id, "delete")
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    image_file = tmp_path / "delete.jpg"
    image_file.write_bytes(b"stored-image")
    scan.image_path = "storage/uploads/delete.jpg"
    db_session.commit()
    scan_id = scan.id

    response = client.delete(
        f"/api/v1/scans/{scan_id}",
        headers=user_headers,
    )

    assert response.status_code == 204
    assert db_session.get(Scan, scan_id) is None
    assert db_session.query(ScanTopK).filter_by(scan_id=scan_id).count() == 0
    assert db_session.query(ScanModelResult).filter_by(scan_id=scan_id).count() == 0
    assert not image_file.exists()
    assert client.get(
        f"/api/v1/scans/{scan_id}", headers=user_headers
    ).status_code == 404


def test_invalid_scan_detail_does_not_return_treatment(
    client,
    db_session,
    normal_user,
    user_headers,
):
    db_session.add(
        DiseaseInfo(
            label_key="Tomato___Early_blight",
            disease_name="Bệnh cháy lá sớm",
            treatment="Không được trả về",
            severity_level="medium",
        )
    )
    db_session.commit()
    scan = create_scan(db_session, normal_user.id, "invalid-treatment")
    scan.is_valid_leaf = False
    db_session.commit()

    response = client.get(f"/api/v1/scans/{scan.id}", headers=user_headers)

    assert response.status_code == 200
    assert response.json()["disease_name"] is None
    assert response.json()["treatment"] is None


def test_scan_detail_tolerates_corrupt_model_topk_json(
    client,
    db_session,
    normal_user,
    user_headers,
):
    scan = create_scan(db_session, normal_user.id, "corrupt-audit")
    model_result = db_session.query(ScanModelResult).filter_by(scan_id=scan.id).one()
    model_result.topk_json = "{not-valid-json"
    db_session.commit()

    response = client.get(f"/api/v1/scans/{scan.id}", headers=user_headers)

    assert response.status_code == 200
    assert response.json()["model_results"][0]["top_k"] == []
