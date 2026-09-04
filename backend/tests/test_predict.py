"""Integration tests cho upload, policy theo role và persistence multi-model."""

import io
import time

import pytest
from PIL import Image
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.models import (
    DiseaseInfo, Farm, FarmMember, Scan, ScanModelResult, ScanTopK,
)
from app.services.predict_service import predict_service


def create_dummy_image(image_format: str = "JPEG") -> io.BytesIO:
    file = io.BytesIO()
    Image.new("RGB", (224, 224), color="green").save(file, image_format)
    file.seek(0)
    return file


def make_result(specs, mode: str, *, accepted: bool = True) -> dict:
    confidence = 0.8 if accepted else 0.2
    status = "accepted" if accepted else "low_confidence"
    model_results = [
        {
            "model_version_id": spec.id,
            "version_name": spec.version_name,
            "model_type": spec.model_type,
            "execution_order": index,
            "predicted_label": "Tomato___Early_blight",
            "confidence": confidence,
            "top1_top2_margin": 0.65 if accepted else 0.02,
            "entropy": 0.2 if accepted else 0.9,
            "energy_score": -3.0,
            "accepted": accepted,
            "latency_ms": 10.0,
            "error_code": None,
            "top_k": [
                {"label": "Tomato___Early_blight", "confidence": confidence, "rank": 1},
                {"label": "Tomato___Late_blight", "confidence": 0.15, "rank": 2},
                {"label": "Tomato___healthy", "confidence": 0.05, "rank": 3},
            ],
        }
        for index, spec in enumerate(specs, start=1)
    ]
    return {
        "label": "Tomato___Early_blight" if accepted else None,
        "candidate_label": "Tomato___Early_blight",
        "confidence": confidence,
        "is_valid_leaf": accepted,
        "top_k": model_results[0]["top_k"],
        "model_version": specs[0].version_name,
        "primary_model_version_id": specs[0].id,
        "inference_mode": mode,
        "validation_status": status,
        "rejection_reason": None if accepted else "confidence_below_threshold",
        "agreement_status": "single_model" if len(specs) == 1 else "agreed",
        "agreement_count": len(specs),
        "models_requested": len(specs),
        "models_succeeded": len(specs),
        "top1_top2_margin": 0.65 if accepted else 0.02,
        "ensemble_entropy": 0.2 if accepted else 0.9,
        "js_divergence": 0.0,
        "energy_score": -3.0,
        "ood_score": 0.2 if accepted else 0.9,
        "policy_version": "ensemble-baseline-v1",
        "model_results": model_results,
    }


@pytest.fixture
def upload_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def mock_prediction(monkeypatch, active_model_versions):
    def fake_predict(_data, specs, mode):
        return make_result(specs, mode)

    monkeypatch.setattr(predict_service, "predict", fake_predict)
    return active_model_versions


def post_image(client, *, headers=None, farm_id=None, mode=None, content_type="image/jpeg"):
    data = {} if farm_id is None else {"farm_id": str(farm_id)}
    if mode is not None:
        data["mode"] = mode
    return client.post(
        "/api/v1/predict",
        files={"file": ("leaf.jpg", create_dummy_image(), content_type)},
        data=data,
        headers=headers or {},
    )


def test_predict_rejects_wrong_mime_and_corrupt_image(client):
    wrong_type = client.post(
        "/api/v1/predict",
        files={"file": ("document.txt", b"Test data", "text/plain")},
    )
    corrupt = client.post(
        "/api/v1/predict",
        files={"file": ("fake.jpg", b"not-an-image", "image/jpeg")},
    )
    assert wrong_type.status_code == 415
    assert corrupt.status_code == 422


def test_predict_rejects_mime_spoof_and_oversized_upload(client, monkeypatch):
    spoofed = client.post(
        "/api/v1/predict",
        files={"file": ("claimed.png", create_dummy_image("JPEG"), "image/png")},
    )
    monkeypatch.setattr(settings, "MAX_UPLOAD_BYTES", 10)
    oversized = post_image(client)
    assert spoofed.status_code == 415
    assert oversized.status_code == 413


def test_capabilities_and_role_mode_enforcement(
    client, active_model_versions, user_headers, technician_headers
):
    guest = client.get("/api/v1/predict/capabilities").json()
    user = client.get("/api/v1/predict/capabilities", headers=user_headers).json()
    technician = client.get(
        "/api/v1/predict/capabilities", headers=technician_headers
    ).json()
    assert guest["allowed_modes"] == ["basic"]
    assert user["default_mode"] == "standard"
    assert technician["default_mode"] == "advanced"
    assert post_image(client, mode="advanced").status_code == 403
    assert post_image(client, headers=user_headers, mode="advanced").status_code == 403


def test_guest_uses_basic_without_creating_scan(client, db_session, mock_prediction):
    response = post_image(client)
    assert response.status_code == 200
    body = response.json()
    assert body["inference_mode"] == "basic"
    assert body["models_requested"] == 1
    assert body["scan_id"] is None
    assert body["farm_assignment_status"] == "not_applicable"
    assert db_session.query(Scan).count() == 0


def test_guest_cannot_submit_farm_id(client):
    assert post_image(client, farm_id=1).status_code == 400


def test_authenticated_standard_persists_scan_top3_and_two_model_results(
    client, db_session, normal_user, user_headers, upload_dir, mock_prediction
):
    db_session.add(
        DiseaseInfo(
            label_key="Tomato___Early_blight",
            disease_name="Bệnh cháy lá sớm",
            treatment="Loại bỏ lá bệnh",
            severity_level="medium",
        )
    )
    db_session.commit()
    response = post_image(client, headers=user_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["inference_mode"] == "standard"
    assert body["models_requested"] == 2
    assert body["disease_name"] == "Bệnh cháy lá sớm"
    scan = db_session.query(Scan).one()
    assert scan.user_id == normal_user.id
    assert scan.primary_model_version_id is not None
    assert db_session.query(ScanTopK).filter_by(scan_id=scan.id).count() == 3
    assert db_session.query(ScanModelResult).filter_by(scan_id=scan.id).count() == 2
    assert len(list(upload_dir.iterdir())) == 1


def test_technician_auto_uses_three_models(
    client, technician_headers, upload_dir, mock_prediction
):
    response = post_image(client, headers=technician_headers)
    assert response.status_code == 200
    assert response.json()["inference_mode"] == "advanced"
    assert response.json()["models_requested"] == 3


def test_manager_and_managed_user_can_assign_authorized_farm(
    client, db_session, manager_user, manager_headers, user_factory,
    token_headers, upload_dir, mock_prediction,
):
    farm = Farm(owner_id=manager_user.id, name="Farm hợp lệ")
    managed_user = user_factory("managed_predict", created_by=manager_user.id)
    db_session.add(farm)
    db_session.flush()
    db_session.add(FarmMember(farm_id=farm.id, user_id=managed_user.id, added_by=manager_user.id))
    db_session.commit()
    manager_response = post_image(client, headers=manager_headers, farm_id=farm.id)
    managed_response = post_image(
        client, headers=token_headers(managed_user), farm_id=farm.id
    )
    assert manager_response.json()["farm_assignment_status"] == "assigned"
    assert managed_response.json()["farm_assignment_status"] == "assigned"
    assert db_session.query(Scan).filter_by(farm_id=farm.id).count() == 2


def test_unauthorized_farm_warns_but_persists(
    client, db_session, manager_user, normal_user, user_headers,
    upload_dir, mock_prediction,
):
    farm = Farm(owner_id=manager_user.id, name="Farm không được gán")
    db_session.add(farm)
    db_session.commit()
    response = post_image(client, headers=user_headers, farm_id=farm.id)
    assert response.status_code == 200
    assert response.json()["farm_assignment_status"] == "not_allowed"
    assert response.json()["warning"]
    assert db_session.query(Scan).one().farm_id is None


def test_low_confidence_returns_no_label_or_treatment(
    client, db_session, monkeypatch, active_model_versions
):
    db_session.add(
        DiseaseInfo(
            label_key="Tomato___Early_blight",
            disease_name="Bệnh cháy lá sớm",
            treatment="Không được hiển thị",
            severity_level="medium",
        )
    )
    db_session.commit()
    monkeypatch.setattr(
        predict_service,
        "predict",
        lambda _data, specs, mode: make_result(specs, mode, accepted=False),
    )
    response = post_image(client)
    assert response.status_code == 200
    assert response.json()["label"] is None
    assert response.json()["validation_status"] == "low_confidence"
    assert response.json()["treatment"] is None
    assert response.json()["warning"]


def test_invalid_bearer_is_not_silently_treated_as_guest(client):
    assert post_image(
        client, headers={"Authorization": "Bearer invalid-token"}
    ).status_code == 401


def test_missing_active_model_is_service_unavailable(client):
    response = post_image(client)
    assert response.status_code == 503
    assert "model" in response.json()["detail"]


def test_inference_timeout_and_error_do_not_leak_internal_details(
    client, monkeypatch, active_model_versions
):
    monkeypatch.setattr(settings, "INFERENCE_TIMEOUT_SECONDS", 0.001)
    monkeypatch.setattr(
        predict_service, "predict", lambda _data, _specs, _mode: time.sleep(0.05)
    )
    assert post_image(client).status_code == 504
    monkeypatch.setattr(settings, "INFERENCE_TIMEOUT_SECONDS", 30.0)

    def fail_inference(_data, _specs, _mode):
        raise RuntimeError("secret model filesystem detail")

    monkeypatch.setattr(predict_service, "predict", fail_inference)
    failed = post_image(client)
    assert failed.status_code == 503
    assert "secret" not in failed.text


def test_db_failure_rolls_back_and_removes_saved_file(
    client, db_session, user_headers, upload_dir, mock_prediction, monkeypatch
):
    def fail_commit() -> None:
        raise SQLAlchemyError("db unavailable")

    monkeypatch.setattr(db_session, "commit", fail_commit)
    response = post_image(client, headers=user_headers)
    assert response.status_code == 500
    assert list(upload_dir.iterdir()) == []
    assert db_session.query(Scan).count() == 0
