"""Opt-in real-weight API test. Uses only isolated pytest DB and upload fixtures."""

import hashlib
import json
import os
from pathlib import Path
import time

import pytest
import torch

from app.core.config import BASE_DIR, settings
from app.models import ModelVersion, Scan
from app.services.model_artifact_service import discover_artifacts
from tests.test_predict import upload_dir


@pytest.mark.skipif(not os.getenv("PREDICT_SAMPLE_AUDIT"), reason="Opt-in downloaded-image/real-weight audit")
def test_downloaded_samples_through_predict_api(client, db_session, admin_headers, upload_dir):
    root = BASE_DIR / "docs" / "predict-selection-audit"
    output = root / os.environ["PREDICT_SAMPLE_AUDIT"]
    if not output.resolve().is_relative_to(root.resolve()) or output.exists():
        raise ValueError("Report must be a new file in audit directory")
    samples = json.loads((root / "samples.json").read_text(encoding="utf-8"))
    artifacts = discover_artifacts(settings.MODEL_ARTIFACT_ROOT)
    for artifact in artifacts:
        db_session.add(ModelVersion(version_name=artifact.version_name, model_type=artifact.model_type,
            file_path=artifact.file_path, classes_path=artifact.classes_path, task=artifact.task,
            temperature_path=artifact.temperature_path, temperature=artifact.temperature,
            sha256=artifact.sha256, is_active=True, is_enabled=True))
    db_session.commit()
    variants = [{"mode": mode} for mode in ("basic", "standard", "advanced")]
    if os.getenv("PREDICT_SAMPLE_SINGLE"):
        variants += [{"mode": "advanced", "strategy": "single", "model_type": kind}
                     for kind in ("efficientnet_b0", "mobilenet_v2", "resnet50")]
    rows = []
    previous_threads = torch.get_num_threads()
    torch.set_num_threads(2)
    try:
        for sample in samples:
            path = root / sample["path"]
            data = path.read_bytes()
            assert hashlib.sha256(data).hexdigest() == sample["sha256"]
            for variant in variants:
                started = time.perf_counter()
                response = client.post("/api/v1/predict", headers=admin_headers, data=variant,
                    files={"file": (path.name, data, "image/png" if path.suffix == ".png" else "image/jpeg")})
                body = response.json()
                rows.append({"sample": sample["name"], "group": sample["group"],
                             "expected_label": sample["expected_label"], "request": variant,
                             "http_status": response.status_code, "seconds": time.perf_counter() - started,
                             "response": body})
                assert response.status_code == 200, body
                assert body["models_succeeded"] == body["models_requested"]
                detail = client.get(f"/api/v1/scans/{body['scan_id']}", headers=admin_headers)
                assert detail.status_code == 200
                assert detail.json()["validation_status"] == body["validation_status"]
                if body["validation_status"] != "accepted":
                    assert body["label"] is None and body["treatment"] is None
                    assert detail.json()["treatment"] is None
        assert db_session.query(Scan).count() == len(rows)
    finally:
        torch.set_num_threads(previous_threads)
        with output.open("x", encoding="utf-8") as stream:
            json.dump({"not_an_independent_accuracy_benchmark": True,
                       "artifacts": [{"model": a.model_type, "version": a.version_name,
                                      "sha256": a.sha256, "temperature": a.temperature} for a in artifacts],
                       "rows": rows}, stream, ensure_ascii=False, indent=2, allow_nan=False)
