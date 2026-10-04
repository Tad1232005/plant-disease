"""Unit and integration tests for two-stage cascade inference with primary model selection."""

import io
import pytest
from PIL import Image

from app.core.config import settings
from app.services.predict_service import (
    ActiveModelSpec,
    PredictService,
    get_active_models,
)
from tests.test_predict import create_dummy_image, make_result, mock_prediction, upload_dir


def image_bytes() -> bytes:
    stream = io.BytesIO()
    Image.new("RGB", (64, 64), color="green").save(stream, "JPEG")
    return stream.getvalue()


def dummy_specs(count: int, primary: str = "efficientnet_b0") -> list[ActiveModelSpec]:
    types = ["efficientnet_b0", "mobilenet_v2", "resnet50"]
    if primary in types:
        types.remove(primary)
        ordered_types = [primary] + types
    else:
        ordered_types = types
    return [
        ActiveModelSpec(
            id=index + 1,
            version_name=f"{model_type}-v1",
            model_type=model_type,
            file_path="unused.pt",
            classes_path="unused.json",
            temperature=1.0,
            sha256=None,
        )
        for index, model_type in enumerate(ordered_types[:count])
    ]


def fake_result_with_probs(spec, order: int, probs: list[float]):
    classes = [f"class-{index}" for index in range(len(probs))]
    ranked = sorted(range(len(probs)), key=lambda index: probs[index], reverse=True)
    return {
        "model_version_id": spec.id,
        "version_name": spec.version_name,
        "model_type": spec.model_type,
        "execution_order": order,
        "predicted_label": classes[ranked[0]],
        "confidence": probs[ranked[0]],
        "top1_top2_margin": probs[ranked[0]] - probs[ranked[1]],
        "entropy": 0.1,
        "energy_score": -2.0,
        "accepted": True,
        "latency_ms": 1.0,
        "error_code": None,
        "top_k": [
            {"label": classes[index], "confidence": probs[index], "rank": rank}
            for rank, index in enumerate(ranked[:3], start=1)
        ],
        "all_probs": probs,
        "classes": classes,
    }


def test_stage_1_high_confidence_exits_early_without_running_stage_2(monkeypatch):
    """Khi Primary model rất tự tin (>= high_conf_msp), trả về ngay ở Tầng 1."""
    service = PredictService()
    monkeypatch.setattr(settings, "PARALLEL_MODEL_INFERENCE", False)

    executed_orders = []

    def tracking_predict(_tensor, spec, order):
        executed_orders.append(order)
        # 0.99 > high_conf_msp (0.9852)
        return fake_result_with_probs(spec, order, [0.99, 0.008, 0.002])

    monkeypatch.setattr(service, "_safe_predict_one", tracking_predict)

    specs = dummy_specs(3)
    result = service.predict(image_bytes(), specs, "advanced")

    assert result["validation_status"] == "accepted"
    assert result["is_valid_leaf"] is True
    assert result["models_requested"] == 3
    assert result["models_succeeded"] == 1
    assert result["decision_details"]["stage_reached"] == 1
    assert result["decision_details"]["ood_method"] == "high_confidence"
    # Chỉ duy nhất order 1 (Primary model) được chạy
    assert executed_orders == [1]


def test_stage_1_low_confidence_rejects_without_running_stage_2(monkeypatch):
    """Khi Primary model quá phân vân (< low_conf_msp), từ chối ngay ở Tầng 1."""
    service = PredictService()
    monkeypatch.setattr(settings, "PARALLEL_MODEL_INFERENCE", False)

    executed_orders = []

    def tracking_predict(_tensor, spec, order):
        executed_orders.append(order)
        # 0.4 < low_conf_msp (0.508)
        return fake_result_with_probs(spec, order, [0.4, 0.35, 0.25])

    monkeypatch.setattr(service, "_safe_predict_one", tracking_predict)

    specs = dummy_specs(3)
    result = service.predict(image_bytes(), specs, "advanced")

    assert result["validation_status"] == "low_confidence"
    assert result["is_valid_leaf"] is False
    assert result["label"] is None
    assert result["rejection_reason"] == "confidence_below_threshold"
    assert result["models_succeeded"] == 1
    assert result["decision_details"]["stage_reached"] == 1
    assert result["decision_details"]["ood_method"] == "low_confidence"
    assert executed_orders == [1]


def test_stage_2_triggers_when_primary_is_in_uncertain_zone(monkeypatch):
    """Khi Primary model rơi vào vùng lửng (0.508 <= msp < 0.985), Tầng 2 kích hoạt."""
    service = PredictService()
    monkeypatch.setattr(settings, "PARALLEL_MODEL_INFERENCE", False)

    executed_orders = []

    def tracking_predict(_tensor, spec, order):
        executed_orders.append(order)
        # 0.85 nằm trong vùng lửng (0.508 - 0.985)
        return fake_result_with_probs(spec, order, [0.85, 0.1, 0.05])

    monkeypatch.setattr(service, "_safe_predict_one", tracking_predict)

    specs = dummy_specs(3)
    result = service.predict(image_bytes(), specs, "advanced")

    assert result["validation_status"] == "accepted"
    assert result["models_requested"] == 3
    assert result["models_succeeded"] == 3
    assert result["decision_details"]["stage_reached"] == 2
    assert result["decision_details"]["ood_method"] == "ensemble"
    # Cả 3 model đều được chạy
    assert executed_orders == [1, 2, 3]


def test_primary_model_selection_order_in_db(db_session, active_model_versions):
    """Kiểm tra cờ primary_model thay đổi thứ tự ưu tiên Tầng 1."""
    # Mặc định: efficientnet_b0 là primary (index 0)
    default_models = get_active_models(db_session, "standard")
    assert default_models[0].model_type == "efficientnet_b0"

    # Chỉ định primary_model = mobilenet_v2
    custom_models = get_active_models(db_session, "standard", primary_model="mobilenet_v2")
    assert custom_models[0].model_type == "mobilenet_v2"
    assert custom_models[1].model_type == "efficientnet_b0"


def test_api_primary_model_flag(client, technician_headers, mock_prediction):
    """API predict nhận cờ primary_model cho ensemble."""
    response = client.post(
        "/api/v1/predict",
        headers=technician_headers,
        data={"strategy": "ensemble", "primary_model": "mobilenet_v2"},
        files={"file": ("leaf.jpg", create_dummy_image(), "image/jpeg")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["inference_strategy"] == "ensemble"
    assert body["selected_model_type"] == "mobilenet_v2"


def test_api_rejects_primary_model_in_single_strategy(client, technician_headers):
    """API từ chối nếu truyền cả primary_model và strategy=single."""
    response = client.post(
        "/api/v1/predict",
        headers=technician_headers,
        data={
            "strategy": "single",
            "model_type": "resnet50",
            "primary_model": "mobilenet_v2",
        },
        files={"file": ("leaf.jpg", create_dummy_image(), "image/jpeg")},
    )
    assert response.status_code == 422
