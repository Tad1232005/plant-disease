"""
Chia data/filtered/ thành train/val/test theo leaf_id (tránh leakage).

- Tải leaf-map.json từ Hugging Face nếu chưa có (cache: data/metadata/)
- Lọc class theo target_classes trong config.yaml
- Gom ảnh cùng lá → chia leaf vào train/val/test (stratified theo class)

Cách dùng:
    python ml/src/split_dataset.py
"""

import json
import random
import re
import shutil
from collections import defaultdict
from pathlib import Path

from huggingface_hub import hf_hub_download

from config import load_config, ml_path

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}
LEAF_MAP_HF_PATH = "leaf_grouping/leaf-map.json"


def load_leaf_map(cfg: dict) -> dict:
    metadata_dir = ml_path(cfg["paths"]["metadata_dir"])
    local_path = metadata_dir / "leaf-map.json"
    repo_id = cfg["huggingface"]["dataset_name"]

    if not local_path.exists():
        metadata_dir.mkdir(parents=True, exist_ok=True)
        print(f"Đang tải {LEAF_MAP_HF_PATH} từ Hugging Face...")
        cached = hf_hub_download(repo_id, LEAF_MAP_HF_PATH, repo_type="dataset")
        local_path.write_bytes(Path(cached).read_bytes())
        print(f"Đã lưu: {local_path.resolve()}")

    with open(local_path, encoding="utf-8") as f:
        return json.load(f)


def _build_leaf_index(leaf_map: dict) -> dict[str, list[str]]:
    by_num: dict[str, list[str]] = defaultdict(list)
    for leaf_id in leaf_map:
        match = re.search(r"(\d+)\s*$", leaf_id)
        if match:
            by_num[match.group(1)].append(leaf_id)
    return by_num


def resolve_leaf_id(class_name: str, filename: str, leaf_map: dict, by_num: dict) -> str:
    stem = Path(filename).stem
    for token in (" copy", " Copy"):
        stem = stem.replace(token, "")

    suffix = stem.split("___", 1)[1] if "___" in stem else stem
    direct = suffix.lower()
    if direct in leaf_map:
        return direct

    match = re.search(r"(\d+(?:\.\d+)?)\s*$", suffix)
    if match:
        num = match.group(1).split(".")[0]
        class_prefix = f"{class_name}:::"
        for leaf_id in by_num.get(num, []):
            if any(entry.startswith(class_prefix) for entry in leaf_map[leaf_id]):
                return leaf_id

    return f"__solo__{class_name}::{stem}"


def _copy_images(files: list[Path], dest_class_dir: Path) -> int:
    dest_class_dir.mkdir(parents=True, exist_ok=True)
    copied = 0
    for src in files:
        dest = dest_class_dir / src.name
        if dest.exists():
            stem, suffix = src.stem, src.suffix
            counter = 1
            while dest.exists():
                dest = dest_class_dir / f"{stem}_{counter}{suffix}"
                counter += 1
        shutil.copy2(src, dest)
        copied += 1
    return copied


def split_dataset():
    cfg = load_config()
    filtered_dir = ml_path(cfg["paths"]["filtered_dir"])
    split_dir = ml_path(cfg["paths"]["split_dir"])
    target_classes = set(cfg["target_classes"])

    train_ratio = cfg["split"]["train_ratio"]
    val_ratio = cfg["split"]["val_ratio"]
    test_ratio = cfg["split"]["test_ratio"]
    seed = cfg["split"]["seed"]

    if abs(train_ratio + val_ratio + test_ratio - 1.0) > 1e-6:
        raise ValueError("train_ratio + val_ratio + test_ratio phải bằng 1.0")

    if not filtered_dir.exists():
        raise FileNotFoundError(
            f"Không tìm thấy {filtered_dir}. Chạy download_dataset.py trước."
        )

    invalid = target_classes - {
        d.name for d in filtered_dir.iterdir() if d.is_dir()
    }
    if invalid:
        raise ValueError(
            "target_classes không tồn tại trong filtered/:\n"
            + "\n".join(f"  - {name}" for name in sorted(invalid))
        )

    leaf_map = load_leaf_map(cfg)
    by_num = _build_leaf_index(leaf_map)

    random.seed(seed)

    for subset in ("train", "val", "test"):
        subset_path = split_dir / subset
        if subset_path.exists():
            shutil.rmtree(subset_path)

    print("=" * 60)
    print("Chia tập train / val / test (theo leaf)")
    print("=" * 60)
    print(f"Nguồn:          {filtered_dir}")
    print(f"Đích:           {split_dir}")
    print(f"Class scope:    {len(target_classes)} class")
    print(f"Tỷ lệ (leaf):   {train_ratio:.0%} / {val_ratio:.0%} / {test_ratio:.0%}\n")

    mapped_leaf_ids: set[str] = set()
    solo_leaf_ids: set[str] = set()
    totals = {"train": 0, "val": 0, "test": 0}

    for class_name in sorted(target_classes):
        class_dir = filtered_dir / class_name
        images = [
            p for p in class_dir.glob("*")
            if p.suffix.lower() in IMAGE_SUFFIXES
        ]
        if not images:
            print(f"  [BỎ QUA] {class_name}: không có ảnh")
            continue

        leaf_groups: dict[str, list[Path]] = defaultdict(list)
        for img in images:
            leaf_id = resolve_leaf_id(class_name, img.name, leaf_map, by_num)
            leaf_groups[leaf_id].append(img)

        for leaf_id in leaf_groups:
            if leaf_id.startswith("__solo__"):
                solo_leaf_ids.add(leaf_id)
            else:
                mapped_leaf_ids.add(leaf_id)

        leaf_ids = list(leaf_groups.keys())
        random.shuffle(leaf_ids)

        n = len(leaf_ids)
        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)
        n_test = n - n_train - n_val

        partitions = {
            "train": leaf_ids[:n_train],
            "val": leaf_ids[n_train:n_train + n_val],
            "test": leaf_ids[n_train + n_val:],
        }

        class_counts = {"train": 0, "val": 0, "test": 0}
        for subset, leaves in partitions.items():
            dest_class_dir = split_dir / subset / class_name
            for leaf_id in leaves:
                class_counts[subset] += _copy_images(leaf_groups[leaf_id], dest_class_dir)

        totals["train"] += class_counts["train"]
        totals["val"] += class_counts["val"]
        totals["test"] += class_counts["test"]

        print(
            f"  {class_name}: leaves={n} | "
            f"train={class_counts['train']} img, "
            f"val={class_counts['val']} img, "
            f"test={class_counts['test']} img"
        )

    print("\n" + "=" * 60)
    print("HOÀN TẤT")
    print("=" * 60)
    print(f"\nOutput: {split_dir.resolve()}")
    print(f"Tổng ảnh: train={totals['train']:,}, val={totals['val']:,}, test={totals['test']:,}")
    print(f"Leaf có map: {len(mapped_leaf_ids):,} | fallback solo: {len(solo_leaf_ids):,}")
    print("\nBước tiếp theo:")
    print("  python ml/src/train.py")


if __name__ == "__main__":
    split_dataset()
