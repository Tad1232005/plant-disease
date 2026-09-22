"""Regression tests for safe week-3 fallback without a leaf detector."""

import io

import pytest
import torch
from PIL import Image
from torchvision import transforms

from app.services.predict_service import PredictService, LoadedModel, ModelConfigurationError
from tests.test_ensemble import specs
from tests.test_predict import make_result, post_image, upload_dir, mock_prediction


def test_preprocess_matches_ml_without_crop():
    image = Image.new("RGB", (400, 150), "green")
    image.paste("red", (0, 0, 80, 150))
    expected = transforms.Compose([
        transforms.Resize((224, 224), interpolation=transforms.InterpolationMode.BILINEAR, antialias=True),
        transforms.ToTensor(),
        transforms.Normalize([.485, .456, .406], [.229, .224, .225]),
    ])(image)
    assert torch.equal(PredictService().transform(image), expected)


def test_capabilities_discloses_no_leaf_detector(client):
    response = client.get("/api/v1/predict/capabilities")
    assert response.status_code == 200
    assert response.json()["input_assessment"]["leaf_detection_status"] == "not_performed"


def test_accepted_is_not_leaf_confirmation(client, mock_prediction):
    response = post_image(client)
    assert response.status_code == 200
    assert response.json()["is_valid_leaf"] is True  # legacy contract retained
    assert response.json()["input_assessment"]["leaf_detection_status"] == "not_performed"
    assert response.json()["warning"]


@pytest.mark.parametrize("status", ["low_confidence", "ambiguous", "model_error"])
def test_status_overrides_inconsistent_legacy_flag(client, active_model_versions, monkeypatch, status):
    from app.services.predict_service import predict_service
    def inconsistent(_data, versions, mode):
        result = make_result(versions, mode)
        result["validation_status"] = status
        return result
    monkeypatch.setattr(predict_service, "predict", inconsistent)
    response = post_image(client)
    assert response.status_code == 200
    assert response.json()["label"] is None
    assert response.json()["is_valid_leaf"] is False
    assert response.json()["treatment"] is None


def test_truncated_jpeg_rejected_before_inference(client):
    stream = io.BytesIO()
    Image.new("RGB", (224, 224), "green").save(stream, "JPEG")
    response = client.post("/api/v1/predict", files={
        "file": ("broken.jpg", stream.getvalue()[:-100], "image/jpeg"),
    })
    assert response.status_code == 422


@pytest.mark.parametrize("output", [torch.tensor([[float("nan"), 1.]]), torch.zeros(1, 3)])
def test_bad_logits_fail_closed(monkeypatch, output):
    class BadModel(torch.nn.Module):
        def forward(self, tensor):
            return output
    service = PredictService()
    monkeypatch.setattr(service, "_load", lambda spec: LoadedModel(BadModel(), ["a", "b"]))
    with pytest.raises(ModelConfigurationError):
        service._predict_one(torch.zeros(1, 3, 224, 224), specs(1)[0])


def test_nonfinite_result_not_persisted(client, user_headers, db_session, upload_dir,
                                      active_model_versions, monkeypatch):
    from app.models import Scan
    from app.services.predict_service import predict_service
    def invalid(_data, versions, mode):
        result = make_result(versions, mode)
        result["model_results"][0]["energy_score"] = float("inf")
        return result
    monkeypatch.setattr(predict_service, "predict", invalid)
    assert post_image(client, headers=user_headers).status_code == 500
    assert db_session.query(Scan).count() == 0
    assert not list(upload_dir.iterdir())


def test_report_keeps_missing_groups_unknown():
    from scripts.evaluate_input_policy import summarize
    result = summarize([{"mode": "basic", "group": "non_leaf", "status": "accepted"}])
    assert result["basic"]["false_accept_rate"] == 1.0
    assert result["basic"]["accuracy_among_accepted"] is None
    assert result["advanced"]["false_accept_rate"] is None


def test_report_counts_rejections_and_wrong_accepted_labels():
    from scripts.evaluate_input_policy import summarize
    rows = [{"mode": "basic", "group": "in_scope", "status": status,
             "label": label, "expected_label": "a"}
            for status, label in [("accepted", "a"), ("accepted", "b"), ("ambiguous", None)]]
    result = summarize(rows)["basic"]
    assert result["accuracy_among_accepted"] == .5
    assert result["in_scope_rejection_rate"] == pytest.approx(1 / 3)
