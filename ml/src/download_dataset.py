"""
Bước 1 — Tải PlantVillage (data.zip) từ Hugging Face, export ảnh RGB ra disk.

Dataset: https://huggingface.co/datasets/mohanty/PlantVillage

HF hiện chỉ còn config 'default' (manifest text paths). Ảnh thật nằm trong data.zip:
    raw/color/       ~54k ảnh RGB — dùng cho train
    raw/grayscale/   cùng ảnh, xám
    raw/segmented/   cùng ảnh, tách nền

Pipeline file-based:
    download_dataset.py  →  data/filtered/   (38 class — data gốc)
    split_dataset.py     →  data/split/      (lọc class + chia train/val/test)
    train.py             →  đọc data/split/

Cách dùng:
    python ml/src/download_dataset.py
    # hoặc: cd ml && python src/download_dataset.py
"""

import shutil
import zipfile
from collections import defaultdict
from pathlib import Path, PurePosixPath

from huggingface_hub import hf_hub_download
from tqdm import tqdm

from config import load_config, ml_path

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}


def _unique_dest_path(dest_dir: Path, filename: str) -> Path:
    dest_path = dest_dir / filename
    if not dest_path.exists():
        return dest_path

    stem = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 1
    while dest_path.exists():
        dest_path = dest_dir / f"{stem}_{counter}{suffix}"
        counter += 1
    return dest_path


def _list_color_images(zf: zipfile.ZipFile, zip_prefix: str) -> list[str]:
    members = []
    for name in zf.namelist():
        if not name.startswith(zip_prefix):
            continue
        if name.endswith("/"):
            continue
        if PurePosixPath(name).suffix.lower() not in IMAGE_SUFFIXES:
            continue
        members.append(name)
    return members


def download_dataset():
    cfg = load_config()
    hf_cfg = cfg["huggingface"]
    variant = hf_cfg.get("variant", "color")
    repo_id = hf_cfg["dataset_name"]
    output_dir = ml_path(cfg["paths"]["filtered_dir"])
    zip_prefix = f"raw/{variant}/"

    print("=" * 60)
    print("PlantVillage Dataset")
    print("=" * 60)

    print(f"\n[1/2] Đang tải data.zip từ Hugging Face: {repo_id}")
    print(f"      Chỉ export: {zip_prefix} (~54k ảnh RGB, 38 class)")
    print("      (Lần đầu ~2GB, có thể mất vài phút — dùng cache HF nếu đã tải rồi)")

    zip_path = hf_hub_download(repo_id, "data.zip", repo_type="dataset")
    print(f"\n      Zip cache: {zip_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n[2/2] Đang giải nén ảnh ra data/filtered/ ...")
    class_counts: dict[str, int] = defaultdict(int)
    skipped = 0

    with zipfile.ZipFile(zip_path) as zf:
        members = _list_color_images(zf, zip_prefix)
        if not members:
            raise FileNotFoundError(
                f"Không tìm thấy ảnh trong zip với prefix '{zip_prefix}'. "
                f"Kiểm tra lại huggingface.variant trong config.yaml."
            )

        for member in tqdm(members, desc="Exporting images"):
            # raw/color/Tomato___healthy/xxx.JPG
            rel_parts = PurePosixPath(member).relative_to(PurePosixPath(zip_prefix.rstrip("/"))).parts
            if len(rel_parts) < 2:
                continue

            class_name = rel_parts[0]
            filename = rel_parts[-1]
            dest_dir = output_dir / class_name
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / filename

            if dest_path.exists() and dest_path.stat().st_size > 0:
                skipped += 1
                class_counts[class_name] += 1
                continue

            dest_path = _unique_dest_path(dest_dir, filename)

            with zf.open(member) as src, open(dest_path, "wb") as dst:
                shutil.copyfileobj(src, dst)

            class_counts[class_name] += 1

    total = sum(class_counts.values())
    sorted_classes = sorted(class_counts.keys())

    print("\n" + "=" * 60)
    print("HOÀN TẤT")
    print("=" * 60)
    print(f"\nOutput: {output_dir.resolve()}")
    print(f"Tổng: {total:,} ảnh, {len(sorted_classes)} class")
    if skipped:
        print(f"(Bỏ qua {skipped:,} file đã tồn tại — chạy lại an toàn)")

    print("\nSố ảnh theo class:")
    for class_name in sorted_classes:
        print(f"  {class_name}: {class_counts[class_name]:,}")

    print("\nLưu ý:")
    print("- filtered/ = data gốc 38 class (ảnh RGB). Không push lên GitHub.")
    print("- Lọc class theo scope đồ án ở bước split (target_classes trong config.yaml).")
    print("\nBước tiếp theo:")
    print("  python ml/src/split_dataset.py")


if __name__ == "__main__":
    download_dataset()
