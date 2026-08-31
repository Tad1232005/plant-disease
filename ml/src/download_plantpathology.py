"""
Lọc ảnh từ Plant Pathology 2021 (Kaggle) chỉ giữ những ảnh có ĐÚNG 1 nhãn
'frog_eye_leaf_spot' (không kèm nhãn khác như scab/complex/powdery_mildew),
vì đây là tên gọi khác của Apple Black Rot trên lá — tương đương với
Apple___Black_rot trong PlantVillage.

Dataset gốc là multi-label (train.csv có cột 'labels' dạng "scab frog_eye_leaf_spot"
nếu ảnh bị nhiều bệnh cùng lúc) — chỉ lấy ảnh nhãn đơn để khớp đúng định nghĩa
1 nhãn/ảnh của PlantVillage.

Cách dùng:
    python ml/src/filter_plant_pathology.py --csv path/to/train.csv --images path/to/train_images

Yêu cầu đã tải sẵn từ:
    https://www.kaggle.com/competitions/plant-pathology-2021-fgvc8/data
    (hoặc bản 960px: https://www.kaggle.com/datasets/jirkaborovec/plant-pathology-2021-fgvc8-960px)
"""

import argparse
import shutil
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from config import load_config, ml_path

TARGET_LABEL = "frog_eye_leaf_spot"
DEST_CLASS_NAME = "Apple___Black_rot"

# Giới hạn số ảnh giữ lại — dataset gốc có thể lọc ra vài NGHÌN ảnh nhãn đơn
# frog_eye_leaf_spot, nếu giữ hết sẽ khiến Apple___Black_rot trở thành lớp
# NHIỀU ảnh nhất toàn bộ 38 lớp (vượt cả Orange_Haunglongbing: 3854 ảnh),
# gây mất cân bằng ngược và có nguy cơ model thiên vị đoán về lớp này khi
# không chắc chắn (giống hiện tượng từng gặp với Strawberry_Leaf_scorch).
# Giới hạn ở mức tương đương các lớp trung bình hiện có (~800-1200 ảnh).
MAX_IMAGES = 1000


def filter_plant_pathology(csv_path: Path, images_dir: Path):
    cfg = load_config()
    output_dir = ml_path(cfg["paths"].get("manual_add_dir", "data/manual_add")) / DEST_CLASS_NAME
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(csv_path)

    if "labels" not in df.columns:
        raise ValueError(f"Không tìm thấy cột 'labels' trong {csv_path}. Kiểm tra lại file CSV.")

    # Chỉ giữ ảnh có ĐÚNG 1 nhãn, và nhãn đó là frog_eye_leaf_spot
    # (cột labels dạng "scab frog_eye_leaf_spot" nếu đa nhãn, cách nhau bởi dấu cách)
    single_label_mask = df["labels"].apply(lambda x: str(x).strip() == TARGET_LABEL)
    filtered = df[single_label_mask]

    print("=" * 60)
    print("Lọc Plant Pathology 2021 -> Apple___Black_rot")
    print("=" * 60)
    print(f"\nTổng ảnh trong CSV: {len(df):,}")
    print(f"Ảnh nhãn đơn '{TARGET_LABEL}': {len(filtered):,}")

    if len(filtered) > MAX_IMAGES:
        filtered = filtered.sample(n=MAX_IMAGES, random_state=42)
        print(f"Giới hạn xuống còn: {MAX_IMAGES:,} ảnh (tránh mất cân bằng ngược so với các lớp khác)")

    image_col = "image" if "image" in df.columns else df.columns[0]

    copied = 0
    skipped = 0
    for _, row in tqdm(filtered.iterrows(), total=len(filtered), desc="Copy ảnh"):
        filename = row[image_col]
        src_path = images_dir / filename

        if not src_path.exists():
            skipped += 1
            continue

        dest_path = output_dir / filename
        shutil.copy(src_path, dest_path)
        copied += 1

    print(f"\nĐã copy: {copied:,} ảnh -> {output_dir.resolve()}")
    if skipped:
        print(f"Bỏ qua (không tìm thấy file ảnh): {skipped:,}")

    print("\nBước tiếp theo:")
    print("  python ml/src/split_dataset.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, help="Đường dẫn tới train.csv")
    parser.add_argument("--images", required=True, help="Đường dẫn tới thư mục ảnh train_images")
    args = parser.parse_args()

    filter_plant_pathology(Path(args.csv), Path(args.images))