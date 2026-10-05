"""Backfill accuracy/macro F1/ECE cho Model Version đang thiếu số liệu.

Số liệu thật nằm ở file metrics do `ml/src/evaluate.py` sinh ra, ví dụ
`ml/outputs/metrics_efficientnet_b0_f.json`. Script ghép theo `model_type`:
version `efficientnet_b0` ← `metrics_efficientnet_b0*.json`.

Chạy sau khi đã migrate database::

    python -m scripts.backfill_model_metrics
    python -m scripts.backfill_model_metrics --dry-run
    python -m scripts.backfill_model_metrics --force   # ghi đè cả bản ghi đã có số

An toàn khi chạy lại: mặc định chỉ điền vào bản ghi còn NULL và không commit
nếu không có gì thay đổi.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import ModelVersion
from app.services.model_metrics_service import load_metrics

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_METRICS_DIR = REPO_ROOT / "ml" / "outputs"


def find_metrics_file(metrics_dir: Path, model_type: str) -> Path | None:
    """Tìm file metrics khớp model_type (ví dụ metrics_efficientnet_b0_f.json)."""
    matches = sorted(metrics_dir.glob(f"metrics_{model_type}*.json"))
    return matches[0] if matches else None


def backfill(db: Session, *, metrics_dir: Path, force: bool = False, dry_run: bool = False) -> list[str]:
    """Điền chỉ số còn thiếu cho các Model Version; trả về log từng bản ghi."""
    if not metrics_dir.is_dir():
        raise SystemExit(f"Không thấy thư mục metrics: {metrics_dir}")

    lines: list[str] = []
    changed = False
    for version in db.query(ModelVersion).order_by(ModelVersion.id).all():
        if version.accuracy is not None and not force:
            lines.append(f"- bỏ qua {version.version_name}: đã có accuracy={version.accuracy:.4f}")
            continue

        metrics_file = find_metrics_file(metrics_dir, version.model_type)
        if metrics_file is None:
            lines.append(f"- bỏ qua {version.version_name}: không có file metrics cho {version.model_type}")
            continue

        try:
            metrics = load_metrics(metrics_file)
        except ValueError as exc:
            lines.append(f"- lỗi {version.version_name}: {exc}")
            continue

        version.accuracy = metrics["accuracy"]
        version.macro_f1 = metrics["macro_f1"]
        version.ece = metrics["ece"]
        version.metrics_path = metrics["metrics_path"]
        changed = True
        lines.append(
            f"- {version.version_name}: accuracy={metrics['accuracy']} "
            f"macro_f1={metrics['macro_f1']} ece={metrics['ece']} ({metrics_file.name})"
        )

    if not changed or dry_run:
        db.rollback()
        lines.append("(dry-run) không ghi DB" if changed else "Không có bản ghi nào cần cập nhật")
        return lines

    db.commit()
    lines.append("Đã commit thay đổi.")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics-dir", type=Path, default=DEFAULT_METRICS_DIR,
                        help=f"Thư mục chứa file metrics (mặc định: {DEFAULT_METRICS_DIR})")
    parser.add_argument("--force", action="store_true",
                        help="Ghi đè cả bản ghi đã có chỉ số")
    parser.add_argument("--dry-run", action="store_true",
                        help="Chỉ in kế hoạch, không ghi database")
    args = parser.parse_args()

    with SessionLocal() as db:
        for line in backfill(db, metrics_dir=args.metrics_dir, force=args.force, dry_run=args.dry_run):
            print(line)


if __name__ == "__main__":
    main()
