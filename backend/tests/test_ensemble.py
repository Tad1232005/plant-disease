"""Unit tests cho soft-voting, rejection policy và chế độ degraded."""

import io

from PIL import Image
import pytest

from app.core.config import settings
from app.services.predict_service import (
    ActiveModelSpec,
    InferenceCapacityError,
    PredictService,
)


def image_bytes() -> bytes:
    stream = io.BytesIO()
    Image.new("RGB", (64, 64), color="green").save(stream, "JPEG")
    return stream.getvalue()


def specs(count: int) -> list[ActiveModelSpec]:
    types = ["efficientnet_b0", "mobilenet_v2", "resnet50"]
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
        for index, model_type in enumerate(types[:count])
    ]


def fake_result(spec, order: int, probs: list[float], *, error=False):
    classes = [f"class-{index}" for index in range(len(probs))]
    if error:
        return {
            "model_version_id": spec.id,
            "version_name": spec.version_name,
            "model_type": spec.model_type,
            "execution_order": order,
            "predicted_label": None,
            "confidence": None,
            "top1_top2_margin": None,
            "entropy": None,
            "energy_score": None,
            "accepted": False,
            "latency_ms": None,
            "error_code": "inference_failed",
            "top_k": [],
        }
    ranked = sorted(range(len(probs)), key=lambda index: probs[index], reverse=True)
    return {
        "model_version_id": spec.id,
        "version_name": spec.version_name,
        "model_type": spec.model_type,
        "execution_order": order,
        "predicted_label": classes[ranked[0]],
        "confidence": probs[ranked[0]],
        "top1_top2_margin": probs[ranked[0]] - probs[ranked[1]],
        "entropy": 0.2,
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


def test_soft_voting_accepts_when_models_agree(monkeypatch):
    service = PredictService()
    monkeypatch.setattr(settings, "PARALLEL_MODEL_INFERENCE", False)
    monkeypatch.setattr(
        service,
        "_safe_predict_one",
        lambda _tensor, spec, order: fake_result(spec, order, [0.8, 0.15, 0.05]),
    )
    result = service.predict(image_bytes(), specs(3), "advanced")
    assert result["label"] == "class-0"
    assert result["validation_status"] == "accepted"
    assert result["agreement_status"] == "agreed"
    assert result["models_succeeded"] == 3


def test_low_confidence_is_rejected_even_with_model_agreement(monkeypatch):
    service = PredictService()
    monkeypatch.setattr(settings, "PARALLEL_MODEL_INFERENCE", False)
    monkeypatch.setattr(
        service,
        "_safe_predict_one",
        lambda _tensor, spec, order: fake_result(
            spec, order, [0.26, 0.25, 0.25, 0.24]
        ),
    )
    result = service.predict(image_bytes(), specs(2), "standard")
    assert result["label"] is None
    assert result["validation_status"] == "low_confidence"
    assert result["rejection_reason"] == "confidence_below_threshold"


def test_standard_can_degrade_to_one_model(monkeypatch):
    service = PredictService()
    monkeypatch.setattr(settings, "PARALLEL_MODEL_INFERENCE", False)

    def one_failure(_tensor, spec, order):
        return fake_result(
            spec, order, [0.8, 0.15, 0.05], error=(order == 2)
        )

    monkeypatch.setattr(service, "_safe_predict_one", one_failure)
    result = service.predict(image_bytes(), specs(2), "standard")
    assert result["validation_status"] == "accepted"
    assert result["agreement_status"] == "degraded"
    assert result["models_succeeded"] == 1


def test_bounded_inference_rejects_when_capacity_is_exhausted():
    service = PredictService()
    assert service._capacity.acquire(blocking=False)  # pylint: disable=protected-access
    try:
        with pytest.raises(InferenceCapacityError):
            service.predict_bounded(b"not-read", specs(1), "basic")
    finally:
        service._capacity.release()  # pylint: disable=protected-access
