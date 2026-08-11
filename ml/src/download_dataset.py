"""
Tải PlantVillage từ Hugging Face và lọc các lớp theo scope đồ án.

Dataset:
https://huggingface.co/datasets/mohanty/PlantVillage

Cách dùng:

    cd ml
    python src/download_dataset.py

Kết quả:

    ml/data/filtered/
    ├── Tomato___healthy/
    ├── Tomato___Early_blight/
    ├── Tomato___Late_blight/
    ├── Tomato___Leaf_Mold/
    ├── Tomato___Septoria_leaf_spot/
    └── Tomato___Bacterial_spot/

Dataset không được push lên GitHub.
"""

from pathlib import Path

from datasets import load_dataset
from tqdm import tqdm


# ============================================================
# CẤU HÌNH
# ============================================================

# Dataset trên Hugging Face
DATASET_NAME = "mohanty/PlantVillage"

# Dùng ảnh RGB gốc
DATASET_CONFIG = "color"

# Thư mục output
OUTPUT_DIR = Path("data/filtered")

# Các class nằm trong scope đồ án
TARGET_CLASSES = [
    "Tomato___healthy",
    "Tomato___Early_blight",
    "Tomato___Late_blight",
    "Tomato___Leaf_Mold",
    "Tomato___Septoria_leaf_spot",
    "Tomato___Bacterial_spot",
]


# ============================================================
# HÀM CHÍNH
# ============================================================

def download_and_filter_dataset():
    print("=" * 60)
    print("PlantVillage Dataset")
    print("=" * 60)

    print(f"\n[1/3] Đang tải dataset: {DATASET_NAME}")
    print(f"      Configuration: {DATASET_CONFIG}")

    dataset = load_dataset(
        DATASET_NAME,
        DATASET_CONFIG,
    )

    print("\nDataset đã tải:")

    for split_name, split_dataset in dataset.items():
        print(f"  - {split_name}: {len(split_dataset):,} ảnh")

    # --------------------------------------------------------
    # Gộp train + test của Hugging Face
    # --------------------------------------------------------
    #
    # Dataset gốc đã có train/test.
    # Ở bước này ta gộp lại để sau này tự split theo leaf_id.
    #
    # Điều này quan trọng vì cùng một physical leaf có thể có
    # nhiều ảnh. Không được để ảnh cùng leaf xuất hiện ở cả
    # train và test.
    # --------------------------------------------------------

    from datasets import concatenate_datasets

    full_dataset = concatenate_datasets(
        [
            dataset["train"],
            dataset["test"],
        ]
    )

    print(f"\nTổng số ảnh: {len(full_dataset):,}")

    # --------------------------------------------------------
    # Lấy tên class từ label
    # --------------------------------------------------------

    label_feature = full_dataset.features["label"]

    label_names = label_feature.names

    print(f"Số class trong dataset: {len(label_names)}")

    # Kiểm tra TARGET_CLASSES
    print("\nKiểm tra TARGET_CLASSES:")

    invalid_classes = []

    for class_name in TARGET_CLASSES:
        if class_name in label_names:
            print(f"  [OK] {class_name}")
        else:
            print(f"  [LỖI] Không tìm thấy: {class_name}")
            invalid_classes.append(class_name)

    if invalid_classes:
        raise ValueError(
            "\nCác class sau không tồn tại trong dataset:\n"
            + "\n".join(f"  - {name}" for name in invalid_classes)
        )

    # --------------------------------------------------------
    # Chuyển tên class -> label ID
    # --------------------------------------------------------

    target_label_ids = [
        label_names.index(class_name)
        for class_name in TARGET_CLASSES
    ]

    # --------------------------------------------------------
    # Filter dataset
    # --------------------------------------------------------

    print("\n[2/3] Đang lọc dataset...")

    filtered_dataset = full_dataset.filter(
        lambda example: example["label"] in target_label_ids,
        desc="Filtering target classes",
    )

    print(
        f"Đã lọc: {len(filtered_dataset):,} ảnh "
        f"thuộc {len(TARGET_CLASSES)} class."
    )

    # --------------------------------------------------------
    # Tạo thư mục output
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Export ảnh
    # --------------------------------------------------------

    print("\n[3/3] Đang lưu ảnh...")

    class_counts = {
        class_name: 0
        for class_name in TARGET_CLASSES
    }

    for example in tqdm(
        filtered_dataset,
        desc="Exporting images",
    ):
        label_id = example["label"]

        class_name = label_names[label_id]

        class_dir = OUTPUT_DIR / class_name
        class_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        image = example["image"]

        # Đảm bảo RGB
        if image.mode != "RGB":
            image = image.convert("RGB")

        # image_path có dạng:
        # raw/color/Tomato___healthy/xxxxx.JPG
        original_path = example["image_path"]

        filename = Path(original_path).name

        output_path = class_dir / filename

        # Tránh overwrite nếu có filename trùng
        if output_path.exists():
            stem = output_path.stem
            suffix = output_path.suffix

            counter = 1

            while output_path.exists():
                output_path = (
                    class_dir
                    / f"{stem}_{counter}{suffix}"
                )

                counter += 1

        image.save(output_path)

        class_counts[class_name] += 1

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("HOÀN TẤT")
    print("=" * 60)

    print(f"\nOutput: {OUTPUT_DIR.resolve()}")

    print("\nSố ảnh theo class:")

    for class_name, count in class_counts.items():
        print(f"  {class_name}: {count:,}")

    print("\nDataset structure:")

    for class_name in TARGET_CLASSES:
        class_dir = OUTPUT_DIR / class_name

        if class_dir.exists():
            print(f"  {class_dir}/")

    print("\nLưu ý:")
    print("- Không push ml/data/ lên GitHub.")
    print("- Có thể nén ml/data/filtered/ để chia sẻ nhóm.")
    print("- Khi split train/val/test, cần dùng leaf_id để tránh data leakage.")


if __name__ == "__main__":
    download_and_filter_dataset()