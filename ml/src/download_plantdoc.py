"""
Bước 1b — Tải PlantDoc (ảnh thực tế, nền phức tạp) từ GitHub, map nhãn sang
đúng tên class của PlantVillage, export ra disk để dùng fine-tune.

Dataset gốc: https://github.com/pratikkayal/PlantDoc-Dataset
    (bản Cropped-PlantDoc — đã crop sẵn theo bounding box, dùng cho classification)

Vì sao cần bước này:
    PlantVillage chụp trong lab (nền sạch, ánh sáng đều) nên model dễ bị overfit
    vào đặc điểm nền/ánh sáng thay vì đặc trưng bệnh lý thật. PlantDoc là ảnh chụp
    ngoài thực tế (nền phức tạp, góc/sáng khác nhau) — dùng để fine-tune tiếp model
    đã train trên PlantVillage, giúp tăng khả năng tổng quát hóa (xem docs/domain-gap.md).

Lưu ý quan trọng:
    PlantDoc chỉ có 27 lớp, KHÔNG map được hết 38 lớp của PlantVillage.
    11 lớp còn thiếu (không có trong PlantDoc) cần tự thu thập thủ công,
    xem docs/manual-data-collection.md — đây cũng là bước diễn tập trước cho
    tính năng "admin thêm dữ liệu training" ở admin/ sau này.

Pipeline file-based:
    download_dataset.py       →  data/filtered/    (PlantVillage gốc, 38 class)
    download_plantdoc.py      →  data/plantdoc/    (PlantDoc, map sang tên class PlantVillage)
    (thủ công)                →  data/manual_add/  (11 class còn thiếu, tự thu thập)
    split_dataset.py          →  data/split/       (gộp + lọc + chia train/val/test)
    train.py / finetune.py    →  đọc data/split/

Cách dùng:
    python ml/src/download_plantdoc.py
    # hoặc: cd ml && python src/download_plantdoc.py
"""

import re
import shutil
import zipfile
from collections import defaultdict
from pathlib import Path

import requests
from tqdm import tqdm

from config import load_config, ml_path

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".JPG", ".JPEG", ".PNG"}

# Dùng ZIP archive thay vì `git clone`: PlantDoc chứa vài file tên có ký tự
# không hợp lệ trên Windows (vd "IMG_1629.JPG?1507122477.jpg" — dấu "?" sót lại
# từ lúc crawl ảnh gốc từ URL web). `git checkout` trên Windows sẽ fail cứng với
# các file này. Tải ZIP rồi tự sanitize tên file lúc giải nén để tránh lỗi này
# trên mọi hệ điều hành.
PLANTDOC_ZIP_URL = "https://github.com/pratikkayal/PlantDoc-Dataset/archive/refs/heads/master.zip"

# Ký tự Windows không cho phép trong tên file: < > : " / \ | ? *
_INVALID_WINDOWS_CHARS = re.compile(r'[<>:"|?*]')


def _sanitize_filename(name: str) -> str:
    """Thay ký tự không hợp lệ trên Windows bằng '_' để giải nén an toàn trên mọi OS."""
    return _INVALID_WINDOWS_CHARS.sub("_", name)

# Map tên lớp PlantDoc -> tên lớp PlantVillage (khớp đúng thư mục trong data/filtered/).
# Lớp nào PlantDoc không có tương ứng thì KHÔNG xuất hiện trong dict này -> bị bỏ qua,
# cần tự thu thập thủ công (xem 11 lớp còn thiếu ở cuối file, biến MISSING_CLASSES).
PLANTDOC_TO_PLANTVILLAGE = {
    "Apple Scab Leaf": "Apple___Apple_scab",
    "Apple leaf": "Apple___healthy",
    "Apple rust leaf": "Apple___Cedar_apple_rust",
    "Bell_pepper leaf": "Pepper,_bell___healthy",
    "Bell_pepper leaf spot": "Pepper,_bell___Bacterial_spot",
    "Blueberry leaf": "Blueberry___healthy",
    "Cherry leaf": "Cherry_(including_sour)___healthy",
    "Corn Gray leaf spot": "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
    "Corn leaf blight": "Corn_(maize)___Northern_Leaf_Blight",
    "Corn rust leaf": "Corn_(maize)___Common_rust_",
    "Peach leaf": "Peach___healthy",
    "Potato leaf early blight": "Potato___Early_blight",
    "Potato leaf late blight": "Potato___Late_blight",
    "Raspberry leaf": "Raspberry___healthy",
    "Soyabean leaf": "Soybean___healthy",
    "Squash Powdery mildew leaf": "Squash___Powdery_mildew",
    "Strawberry leaf": "Strawberry___healthy",
    "Tomato Early blight leaf": "Tomato___Early_blight",
    "Tomato Septoria leaf spot": "Tomato___Septoria_leaf_spot",
    "Tomato leaf": "Tomato___healthy",
    "Tomato leaf bacterial spot": "Tomato___Bacterial_spot",
    "Tomato leaf late blight": "Tomato___Late_blight",
    "Tomato leaf mosaic virus": "Tomato___Tomato_mosaic_virus",
    "Tomato leaf yellow virus": "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato two spotted spider mites leaf": "Tomato___Spider_mites Two-spotted_spider_mite",
    "Tomato mold leaf": "Tomato___Leaf_Mold",
    "grape leaf": "Grape___healthy",
    "grape leaf black rot": "Grape___Black_rot",
}

# 11 lớp PlantVillage KHÔNG có tương ứng trong PlantDoc — cần tự thu thập thủ công
# vào data/manual_add/<class_name>/ (xem docs/manual-data-collection.md)
MISSING_CLASSES = [
    "Apple___Black_rot",
    "Cherry_(including_sour)___Powdery_mildew",
    "Corn_(maize)___healthy",
    "Peach___Bacterial_spot",
    "Potato___healthy",
    "Strawberry___Leaf_scorch",
    "Grape___Esca_(Black_Measles)",
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
    "Orange___Haunglongbing_(Citrus_greening)",
    "Tomato___Target_Spot",
]


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


def _clone_plantdoc(clone_dir: Path) -> None:
    """
    Tải PlantDoc-Dataset bằng ZIP archive (không dùng git clone) để tránh lỗi
    checkout trên Windows do vài file có ký tự '?' trong tên (sanitize khi giải nén).
    """
    if clone_dir.exists() and any(clone_dir.iterdir()):
        print(f"      Đã có sẵn {clone_dir}, bỏ qua tải lại (xóa thư mục nếu muốn tải lại)")
        return

    clone_dir.parent.mkdir(parents=True, exist_ok=True)
    zip_path = clone_dir.parent / "PlantDoc-Dataset.zip"

    print(f"      Đang tải ZIP từ {PLANTDOC_ZIP_URL} ...")
    response = requests.get(PLANTDOC_ZIP_URL, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get("content-length", 0))
    with open(zip_path, "wb") as f, tqdm(
        total=total_size, unit="B", unit_scale=True, desc="      Downloading"
    ) as pbar:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            pbar.update(len(chunk))

    print("      Đang giải nén (tự làm sạch tên file lỗi ký tự trên Windows)...")
    skipped_files = []
    with zipfile.ZipFile(zip_path) as zf:
        # Zip từ GitHub archive luôn có 1 thư mục gốc dạng "PlantDoc-Dataset-master/"
        # -> bóc lớp đó ra để đổ thẳng vào clone_dir cho khớp cấu trúc mong đợi.
        names = zf.namelist()
        root_prefix = names[0].split("/")[0] + "/" if names else ""

        for member in names:
            if member.endswith("/"):
                continue

            rel_path = member[len(root_prefix):] if member.startswith(root_prefix) else member
            if not rel_path:
                continue

            parts = [_sanitize_filename(p) for p in rel_path.split("/")]
            dest_path = clone_dir.joinpath(*parts)
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                with zf.open(member) as src, open(dest_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)
            except OSError:
                skipped_files.append(rel_path)

    zip_path.unlink(missing_ok=True)

    if skipped_files:
        print(f"      Cảnh báo: bỏ qua {len(skipped_files)} file lỗi tên không thể ghi:")
        for name in skipped_files[:5]:
            print(f"        - {name}")

    print(f"      Đã tải và giải nén xong vào {clone_dir}")


def download_plantdoc():
    cfg = load_config()
    raw_clone_dir = ml_path("data/raw/PlantDoc-Dataset")
    output_dir = ml_path(cfg["paths"].get("plantdoc_dir", "data/plantdoc"))

    print("=" * 60)
    print("PlantDoc Dataset (ảnh thực tế, nền phức tạp)")
    print("=" * 60)

    print(f"\n[1/2] Đang clone PlantDoc-Dataset về {raw_clone_dir}")
    _clone_plantdoc(raw_clone_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n[2/2] Đang map nhãn PlantDoc -> PlantVillage và export ảnh...")
    class_counts: dict[str, int] = defaultdict(int)
    skipped_unmapped: dict[str, int] = defaultdict(int)

    # PlantDoc có 2 thư mục con: train/ và test/ — gộp cả 2 lại vì mình sẽ tự
    # chia lại train/val/test theo split_dataset.py cho nhất quán với pipeline hiện có.
    source_splits = [raw_clone_dir / "train", raw_clone_dir / "test"]

    all_class_dirs = []
    for split_dir in source_splits:
        if not split_dir.exists():
            print(f"      Cảnh báo: không thấy {split_dir}, bỏ qua")
            continue
        all_class_dirs.extend([d for d in split_dir.iterdir() if d.is_dir()])

    if not all_class_dirs:
        raise FileNotFoundError(
            f"Không tìm thấy thư mục class nào trong {raw_clone_dir}/train hoặc /test. "
            "Kiểm tra lại đã clone đúng repo chưa."
        )

    for class_dir in tqdm(all_class_dirs, desc="Mapping classes"):
        plantdoc_name = class_dir.name
        pv_name = PLANTDOC_TO_PLANTVILLAGE.get(plantdoc_name)

        if pv_name is None:
            # Lớp này PlantDoc có nhưng không map được sang PlantVillage -> bỏ qua
            n_images = sum(
                1 for f in class_dir.glob("*") if f.suffix in IMAGE_SUFFIXES
            )
            skipped_unmapped[plantdoc_name] += n_images
            continue

        dest_dir = output_dir / pv_name
        dest_dir.mkdir(parents=True, exist_ok=True)

        for img_path in class_dir.glob("*"):
            if img_path.suffix not in IMAGE_SUFFIXES:
                continue

            dest_path = _unique_dest_path(dest_dir, img_path.name)
            shutil.copy(img_path, dest_path)
            class_counts[pv_name] += 1

    total = sum(class_counts.values())
    sorted_classes = sorted(class_counts.keys())

    print("\n" + "=" * 60)
    print("HOÀN TẤT")
    print("=" * 60)
    print(f"\nOutput: {output_dir.resolve()}")
    print(f"Tổng: {total:,} ảnh, {len(sorted_classes)} class đã map thành công")

    print("\nSố ảnh theo class (đã map sang tên PlantVillage):")
    for class_name in sorted_classes:
        print(f"  {class_name}: {class_counts[class_name]:,}")

    if skipped_unmapped:
        print("\nLớp PlantDoc KHÔNG map được (bỏ qua, không nằm trong 38 lớp scope hiện tại):")
        for name, n in sorted(skipped_unmapped.items()):
            print(f"  {name}: {n:,} ảnh")

    print(f"\n11 lớp PlantVillage KHÔNG có trong PlantDoc (cần tự thu thập thủ công):")
    for name in MISSING_CLASSES:
        print(f"  {name}")

    print("\nBước tiếp theo:")
    print("  1. Tự thu thập ảnh cho 11 lớp còn thiếu -> data/manual_add/<class_name>/")
    print("  2. python ml/src/split_dataset.py   (gộp filtered + plantdoc + manual_add, chia lại)")


if __name__ == "__main__":
    download_plantdoc()