# ML — Train model nhận diện bệnh lá cây

## Pipeline (file-based)

Nhóm làm theo luồng **tải → export file → train đọc file**, không load Hugging Face lúc train:

```
download_dataset.py  →  data/filtered/     (38 class — data gốc)
split_dataset.py     →  data/split/        (lọc class + train/val/test)
train.py             →  models/            (best_model.pt + classes.json)
evaluate.py          →  outputs/figures/   (confusion matrix, ...)
```

Cấu trúc thư mục:

```
ml/
├── configs/
│   └── config.yaml          # Hyperparameter, đường dẫn, danh sách class
├── data/                    # gitignore — không push lên GitHub
│   ├── filtered/            # Bước 1: 38 class — data gốc từ HF
│   └── split/               # Bước 2: lọc class + train/val/test
│       ├── train/<class>/
│       ├── val/<class>/
│       └── test/<class>/
├── src/
│   ├── download_dataset.py  # Bước 1: HF → file ảnh
│   ├── split_dataset.py     # Bước 2: chia train/val/test
│   ├── data_loader.py       # Load ảnh từ disk + augment
│   ├── model.py
│   ├── train.py             # Bước 3: huấn luyện
│   └── evaluate.py          # Đánh giá trên tập test
├── models/                  # gitignore — best_model.pt, classes.json
├── outputs/
│   ├── logs/
│   └── figures/
├── notebooks/               # EDA, thử nghiệm nhanh
├── requirements.txt
└── README.md
```

## 1. Setup môi trường

```bash
cd ml
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Tải dataset (38 class — data gốc)

Dataset: [mohanty/PlantVillage](https://huggingface.co/datasets/mohanty/PlantVillage) — script tải `data.zip`, chỉ export `raw/color/`.

Chạy **một lần** (lần đầu ~2GB, vài phút):

```bash
python src/download_dataset.py
# hoặc từ repo root: python ml/src/download_dataset.py
```

Kết quả: `data/filtered/<class_name>/*.jpg` (~54k ảnh RGB, 38 class)

> Không push lên GitHub. Nén `data/filtered/` chia sẻ nhóm qua Drive.

## 3. Split theo leaf + lọc class

`target_classes` trong `configs/config.yaml` quyết định class nào được đưa vào train (hiện: **38 class**).

Script tự tải `leaf-map.json` từ Hugging Face → cache tại `data/metadata/` (gitignore, không push).

Chia **theo leaf** (cùng lá không tách train/test), tỷ lệ 70/15/15:

```bash
python src/split_dataset.py
```

Kết quả: `data/split/{train,val,test}/<class_name>/*.jpg`

Tỷ lệ chỉnh trong `configs/config.yaml` (`split`).

## 4. Train

```bash
python src/train.py
```

Model tốt nhất: `models/best_model.pt` + `models/classes.json`

Hyperparameter (`batch_size`, `epochs`, `lr`, ...) nằm trong `configs/config.yaml`.

## 5. Đánh giá

```bash
python src/evaluate.py
```

In classification report và lưu confusion matrix tại `outputs/figures/confusion_matrix.png`.

## 6. Đưa model sang backend

Copy 2 file sau vào `backend/app/models/`:

- `models/best_model.pt`
- `models/classes.json`

## Ghi chú

- `gradcam.py`, `calibration.py`, `predict.py` — bổ sung sau khi có baseline ổn định.
- Split hiện tại chia theo **leaf_id** (leaf-map từ HF). Ảnh không có map dùng fallback 1 ảnh = 1 leaf.
