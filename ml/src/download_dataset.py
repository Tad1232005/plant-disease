"""
Tải dataset PlantVillage và lọc ra các lớp bệnh nằm trong phạm vi (scope) của đồ án.

Cách dùng:
    1. Tải dataset gốc (chạy 1 lần, ~2GB, chỉ cần 1 người trong nhóm làm):
        git clone https://github.com/spMohanty/PlantVillage-Dataset.git ml/data/PlantVillage-Dataset

    2. Chỉnh danh sách TARGET_CLASSES bên dưới theo phạm vi nhóm đã chốt
       (VD: chỉ lấy lá cà chua với 4-6 loại bệnh + khỏe mạnh).

    3. Chạy script này để copy các lớp cần dùng sang ml/data/filtered/
       (nhẹ hơn, dễ đưa lên Google Drive/Kaggle chia sẻ cho 2 bạn còn lại).

        python ml/src/download_dataset.py
"""

import shutil
from pathlib import Path

# Thư mục chứa dataset gốc sau khi git clone
SOURCE_DIR = Path("ml/data/PlantVillage-Dataset/raw/color")

# Thư mục output sau khi lọc — đây là thứ sẽ đưa lên Drive/Kaggle chia sẻ nhóm
OUTPUT_DIR = Path("ml/data/filtered")

# ĐIỀN danh sách lớp muốn dùng (đúng tên thư mục gốc trong PlantVillage).
# Ví dụ dưới đây là cà chua (Tomato) — 5 bệnh phổ biến + khỏe mạnh.
# Xem danh sách đầy đủ các lớp tại:
# https://github.com/spMohanty/PlantVillage-Dataset/tree/master/raw/color
TARGET_CLASSES = [
    "Tomato___healthy",
    "Tomato___Early_blight",
    "Tomato___Late_blight",
    "Tomato___Leaf_Mold",
    "Tomato___Septoria_leaf_spot",
    "Tomato___Bacterial_spot",
]


def filter_dataset():
    if not SOURCE_DIR.exists():
        raise FileNotFoundError(
            f"Không tìm thấy {SOURCE_DIR}. Hãy git clone dataset gốc trước:\n"
            "git clone https://github.com/spMohanty/PlantVillage-Dataset.git ml/data/PlantVillage-Dataset"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for class_name in TARGET_CLASSES:
        src = SOURCE_DIR / class_name
        dst = OUTPUT_DIR / class_name

        if not src.exists():
            print(f"[BỎ QUA] Không tìm thấy lớp: {class_name}")
            continue

        if dst.exists():
            print(f"[ĐÃ CÓ] {class_name}, bỏ qua")
            continue

        shutil.copytree(src, dst)
        n_images = len(list(dst.glob("*")))
        print(f"[OK] {class_name}: {n_images} ảnh")

    print(f"\nHoàn tất. Dữ liệu đã lọc nằm tại: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    filter_dataset()
