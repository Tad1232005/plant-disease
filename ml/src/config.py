"""Load config.yaml — đường dẫn luôn resolve tương đối thư mục ml/."""

from pathlib import Path

import yaml

ML_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ML_ROOT / "configs" / "config.yaml"


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def ml_path(relative: str) -> Path:
    return ML_ROOT / relative
