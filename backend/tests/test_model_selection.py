"""Role-scoped single selection, compatible ensembles, and decision audit."""

import pytest
import torch

from app.core.config import settings
from app.models import ModelVersion
from app.services.predict_service import LoadedModel, PredictService, predict_service
from tests.test_ensemble import fake_result, image_bytes, specs
from tests.test_predict import create_dummy_image, make_result, mock_prediction, upload_dir


def select(client, headers=None, **data):
    return client.post("/api/v1/predict", headers=headers or {}, data=data,
                       files={"file": ("leaf.jpg", create_dummy_image(), "image/jpeg")})


@pytest.mark.parametrize("data", [
    {"strategy": "single"},
    {"model_type": "mobilenet_v2"},
    {"strategy": "ensemble", "model_type": "resnet50"},
    {"strategy": "single", "model_type": "unknown"},
    {"strategy": "random"},
])
def test_invalid_selection_contract(client, data):
    assert select(client, **data).status_code == 422


@pytest.mark.parametrize("kind", ["mobilenet_v2", "resnet50"])
def test_guest_cannot_select_restricted_model(client, kind):
    assert select(client, strategy="single", model_type=kind).status_code == 403


def test_guest_single_efficientnet(client, mock_prediction):
    response = select(client, strategy="single", model_type="efficientnet_b0")
    assert response.status_code == 200
    body = response.json()
    assert body["scan_id"] is None
    assert body["models_requested"] == 1
    assert body["inference_strategy"] == "single"
    assert body["selected_model_type"] == "efficientnet_b0"


@pytest.mark.parametrize("fixture", ["user_headers", "manager_headers"])
def test_standard_roles_cannot_select_resnet(client, request, fixture):
    headers = request.getfixturevalue(fixture)
    assert select(client, headers, strategy="single", model_type="resnet50").status_code == 403


def test_user_single_mobile_persists_selection(client, user_headers, mock_prediction, upload_dir):
    response = select(client, user_headers, strategy="single", model_type="mobilenet_v2")
    assert response.status_code == 200
    body = response.json()
    assert body["inference_mode"] == "standard"
    assert body["models_requested"] == body["models_succeeded"] == 1
    assert body["model_results"][0]["model_type"] == "mobilenet_v2"
    detail = client.get(f"/api/v1/scans/{body['scan_id']}", headers=user_headers).json()
    assert detail["prediction_context"]["inference_strategy"] == "single"
    assert detail["prediction_context"]["selected_model_type"] == "mobilenet_v2"
    assert len(detail["model_results"]) == 1


def test_single_ignores_unselected_inactive_models(client, admin_headers, active_model_versions,
                                                 db_session, monkeypatch, upload_dir):
    db_session.query(ModelVersion).filter(ModelVersion.model_type != "resnet50").update({"is_active": False})
    db_session.commit()
    def only_selected(_bytes, versions, mode):
        assert len(versions) == 1 and versions[0].model_type == "resnet50"
        return make_result(versions, mode)
    monkeypatch.setattr(predict_service, "predict", only_selected)
    assert select(client, admin_headers, strategy="single", model_type="resnet50").status_code == 200
    assert select(client, admin_headers, strategy="ensemble").status_code == 503


def test_selected_inactive_does_not_fallback(client, user_headers, active_model_versions, db_session):
    db_session.query(ModelVersion).filter_by(model_type="mobilenet_v2").update({"is_active": False})
    db_session.commit()
    assert select(client, user_headers, strategy="single", model_type="mobilenet_v2").status_code == 503


def test_explicit_basic_restricts_admin_selection(client, admin_headers):
    assert select(client, admin_headers, mode="basic", strategy="single", model_type="resnet50").status_code == 403


def test_capabilities_lists_role_scoped_models(client, user_headers):
    guest = client.get("/api/v1/predict/capabilities").json()
    user = client.get("/api/v1/predict/capabilities", headers=user_headers).json()
    assert guest["allowed_model_types"] == ["efficientnet_b0"]
    assert user["allowed_model_types"] == ["efficientnet_b0", "mobilenet_v2"]
    assert user["default_strategy"] == "ensemble"


def test_basic_advanced_accept_standard_reject_is_not_boolean_bug(monkeypatch):
    service = PredictService()
    monkeypatch.setattr(settings, "PARALLEL_MODEL_INFERENCE", False)
    monkeypatch.setattr(settings, "CONFIDENCE_THRESHOLD", .3)
    monkeypatch.setattr(settings, "TOP1_MARGIN_THRESHOLD", .05)
    monkeypatch.setattr(settings, "JS_DIVERGENCE_THRESHOLD", .3)
    def prediction(_tensor, spec, order):
        probs = [.25, .7, .05] if spec.model_type == "mobilenet_v2" else [.7, .25, .05]
        return fake_result(spec, order, probs)
    monkeypatch.setattr(service, "_safe_predict_one", prediction)
    basic = service.predict(image_bytes(), specs(1), "basic")
    standard = service.predict(image_bytes(), specs(2), "standard")
    advanced = service.predict(image_bytes(), specs(3), "advanced")
    assert [item["is_valid_leaf"] for item in (basic, standard, advanced)] == [True, False, True]
    assert standard["rejection_reason"] == "top1_top2_margin_too_small"
    assert "top1_top2_margin_too_small" in standard["decision_details"]["failed_rules"]


def test_advanced_single_is_not_degraded(monkeypatch):
    service = PredictService()
    monkeypatch.setattr(service, "_safe_predict_one", lambda tensor, spec, order: fake_result(spec, order, [.8, .15, .05]))
    result = service.predict(image_bytes(), [specs(3)[2]], "advanced")
    assert result["models_requested"] == result["models_succeeded"] == 1
    assert result["agreement_status"] == "single_model"
    assert result["js_divergence"] == 0


def test_snapshot_of_decision_does_not_change_on_read(client, user_headers, active_model_versions,
                                                   monkeypatch, upload_dir):
    details = {"checks": [{"rule": "confidence_below_threshold", "threshold": .3,
                           "value": .8, "passed": True}], "failed_rules": []}
    def prediction(_data, versions, mode):
        result = make_result(versions, mode)
        result["decision_details"] = details
        return result
    monkeypatch.setattr(predict_service, "predict", prediction)
    response = select(client, user_headers).json()
    monkeypatch.setattr(settings, "CONFIDENCE_THRESHOLD", .99)
    detail = client.get(f"/api/v1/scans/{response['scan_id']}", headers=user_headers).json()
    assert detail["prediction_context"]["decision_details"] == details


def test_individual_model_acceptance_also_checks_margin(monkeypatch):
    class CloseScores(torch.nn.Module):
        def forward(self, tensor):
            return torch.log(torch.tensor([[.49, .48, .03]]))
    service = PredictService()
    monkeypatch.setattr(settings, "CONFIDENCE_THRESHOLD", .3)
    monkeypatch.setattr(settings, "TOP1_MARGIN_THRESHOLD", .05)
    monkeypatch.setattr(service, "_load", lambda spec: LoadedModel(CloseScores(), ["a", "b", "c"]))
    result = service._predict_one(torch.zeros(1, 3, 224, 224), specs(1)[0])
    assert result["confidence"] > .3
    assert result["accepted"] is False


def test_decision_details_lists_all_failed_rules(monkeypatch):
    service = PredictService()
    monkeypatch.setattr(settings, "CONFIDENCE_THRESHOLD", .3)
    monkeypatch.setattr(settings, "TOP1_MARGIN_THRESHOLD", .05)
    monkeypatch.setattr(service, "_safe_predict_one", lambda tensor, spec, order: fake_result(spec, order, [.25] * 4))
    result = service.predict(image_bytes(), specs(1), "basic")
    assert result["rejection_reason"] == "confidence_below_threshold"
    assert result["decision_details"]["failed_rules"] == ["confidence_below_threshold", "top1_top2_margin_too_small"]
