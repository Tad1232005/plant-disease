"""Offline policy audit. No database, training, threshold fitting or ML writes."""

import argparse
import asyncio
import io
import json
from pathlib import Path
from typing import Any

import torch
from fastapi import UploadFile
from starlette.datastructures import Headers
from PIL import Image

from app.core.config import BASE_DIR, settings
from app.services.image_storage_service import validate_upload
from app.services.model_artifact_service import discover_artifacts
from app.services.predict_service import ActiveModelSpec, MODEL_TYPES_BY_MODE, POLICY_VERSION, PredictService


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for mode in MODEL_TYPES_BY_MODE:
        subset = [row for row in rows if row["mode"] == mode]
        negatives = [row for row in subset if row["group"] in {"non_leaf", "unsupported_leaf"}]
        positives = [row for row in subset if row["group"] == "in_scope"]
        accepted = [row for row in positives if row["status"] == "accepted"]
        summary[mode] = {
            "runs": len(subset),
            "negative_count": len(negatives),
            "false_accept_rate": sum(row["status"] == "accepted" for row in negatives) / len(negatives) if negatives else None,
            "in_scope_count": len(positives),
            "in_scope_rejection_rate": sum(row["status"] != "accepted" for row in positives) / len(positives) if positives else None,
            "accuracy_among_accepted": sum(row["label"] == row["expected_label"] for row in accepted) / len(accepted) if accepted else None,
        }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--manifest", type=Path, help="JSON list: path, group, expected_label (required for in_scope)")
    source.add_argument("--synthetic", action="store_true", help="Diagnostic only, not a representative OOD benchmark")
    parser.add_argument("--output", type=Path, required=True, help="New JSON file inside backend; never overwrites")
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(BASE_DIR) or output.exists():
        parser.error("Output phải là file mới bên trong backend")
    samples = []
    if args.synthetic:
        for color in ["white", "black", "green"]:
            stream = io.BytesIO()
            Image.new("RGB", (300, 180), color).save(stream, "PNG")
            samples.append((color, "non_leaf", None, stream.getvalue(), "image/png"))
    else:
        records = json.loads(args.manifest.read_text(encoding="utf-8"))
        if not isinstance(records, list) or not records:
            parser.error("Manifest phải là list không rỗng")
        for record in records:
            path = (args.manifest.parent / record["path"]).resolve()
            group = record["group"]
            if group not in {"in_scope", "non_leaf", "unsupported_leaf"}:
                parser.error("group phải là in_scope, non_leaf hoặc unsupported_leaf")
            if group == "in_scope" and not record.get("expected_label"):
                parser.error("in_scope cần expected_label để tính accuracy")
            if path.stat().st_size > settings.MAX_UPLOAD_BYTES:
                parser.error("Ảnh vượt giới hạn upload")
            samples.append((record["path"], group, record.get("expected_label"), path.read_bytes(),
                            "image/png" if path.suffix.lower() == ".png" else "image/jpeg"))
    artifacts = discover_artifacts(settings.MODEL_ARTIFACT_ROOT)
    for _, group, label, _, _ in samples:
        if group == "in_scope" and label not in artifacts[0].classes:
            parser.error("expected_label không thuộc bundle hiện tại")
    specs = {item.model_type: ActiveModelSpec(i, item.version_name, item.model_type,
             item.file_path, item.classes_path, item.temperature, item.sha256)
             for i, item in enumerate(artifacts, 1)}
    torch.set_num_threads(2)
    service = PredictService()
    rows = []
    for name, group, label, data, mime in samples:
        upload = UploadFile(file=io.BytesIO(data), headers=Headers({"content-type": mime}))
        try:
            asyncio.run(validate_upload(upload))
        finally:
            upload.file.close()
        for mode, model_types in MODEL_TYPES_BY_MODE.items():
            result = service.predict_bounded(data, [specs[kind] for kind in model_types], mode)
            rows.append({"sample": name, "group": group, "expected_label": label, "mode": mode,
                         "status": result["validation_status"], "label": result["label"],
                         "confidence": result["confidence"], "reason": result["rejection_reason"],
                         "models_succeeded": result["models_succeeded"]})
    report = {"policy_version": POLICY_VERSION, "synthetic_only": args.synthetic,
              "leaf_detector": "not_performed", "device": str(service.device),
              "torch_version": str(torch.__version__),
              "thresholds": {"confidence": settings.CONFIDENCE_THRESHOLD,
                             "margin": settings.TOP1_MARGIN_THRESHOLD, "js": settings.JS_DIVERGENCE_THRESHOLD},
              "preprocessing": "RGB; resize 224x224 bilinear antialias; ImageNet normalize; no crop",
              "artifacts": [{"model_type": item.model_type, "version": item.version_name,
                             "sha256": item.sha256, "temperature": item.temperature} for item in artifacts],
              "summary": summarize(rows), "rows": rows}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
