"""Đọc file metrics JSON của bundle ML để điền accuracy/macro_f1/ece cho Model Version.

File do `ml/src/evaluate.py` sinh ra (ví dụ `ml/outputs/metrics_efficientnet_b0_f.json`)
có dạng::

    {"accuracy": 0.9826, "macro_avg": {"f1_score": 0.9723, ...}, ...}

Module chấp nhận cả 2 kiểu key: `macro_avg.f1_score` (đầy đủ) hoặc `macro_f1` (rút gọn).
Giá trị được chuẩn hoá về [0, 1] để khớp CheckConstraint của bảng `model_versions`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

# Các tên khóa có thể gặp trong file metrics do nhóm ML bàn giao.
_ACCURACY_KEYS = ("accuracy", "test_accuracy")
_MACRO_F1_KEYS = ("macro_f1", "f1_macro", "f1")
_ECE_KEYS = ("ece", "expected_calibration_error")


def _as_ratio(value: Any) -> float | None:
    """Chuẩn hoá chỉ số về [0, 1]; trả None nếu không phải số hoặc ngoài miền hợp lệ."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if number < 0:
        return None
    if number > 1:
        # evaluate.py có thể ghi phần trăm (98.26) thay vì tỉ lệ (0.9826).
        number = number / 100
        if number > 1:
            return None
    return number


def _first_ratio(payload: Mapping[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        ratio = _as_ratio(payload.get(key))
        if ratio is not None:
            return ratio
    return None


def load_metrics(metrics_path: str | Path) -> dict[str, float | str | None]:
    """Đọc file metrics JSON và trả về chỉ số đã chuẩn hoá.

    Raises:
        ValueError: file không tồn tại, không phải JSON object, hoặc không có
            chỉ số nào dùng được (accuracy / macro F1 / ECE).
    """
    path = Path(metrics_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Không tìm thấy file metrics: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"File metrics không phải JSON hợp lệ: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"File metrics phải là JSON object: {path}")

    macro_avg = payload.get("macro_avg")
    macro_block: Mapping[str, Any] = macro_avg if isinstance(macro_avg, dict) else {}

    accuracy = _first_ratio(payload, _ACCURACY_KEYS)
    macro_f1 = _first_ratio(payload, _MACRO_F1_KEYS)
    if macro_f1 is None:
        macro_f1 = _first_ratio(macro_block, ("f1_score", "f1"))
    ece = _first_ratio(payload, _ECE_KEYS)

    if accuracy is None and macro_f1 is None and ece is None:
        raise ValueError(f"File metrics thiếu chỉ số hỗ trợ (accuracy/macro F1/ECE): {path}")

    return {
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "ece": ece,
        "metrics_path": str(path),
    }
