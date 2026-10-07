# ML — Train model nhận diện bệnh lá cây

## Pipeline (file-based)

Nhóm làm theo luồng **tải → export file → train đọc file**, không load Hugging Face lúc train.
Chi tiết flow hệ thống: [`docs/FLOW.md`](docs/FLOW.md). Log thực nghiệm dài: `FLOW.local.md` (local, không commit).

```
download_dataset.py  →  data/filtered/     (38 class PlantVillage — data gốc)
split_dataset.py     →  data/split/        (train/val/test 70/15/15 theo leaf_id, seed 42)
train.py             →  models/            (best_model_<suffix>.pt + classes/model_type JSON)
calibration.py       →  models/temperature_<suffix>.json  (temperature scaling)
evaluate.py          →  outputs/figures/   (confusion matrix, metrics)
evaluate_ood.py      →  outputs/ood_threshold.json  (ngưỡng OOD per-tier)
```

Backbone đã train (suffix `_f`): `efficientnet_b0`, `mobilenet_v2`, `resnet50`.
OOD gating theo tier (`basic` 1 model / `standard` 2 / `advanced` 3, primary EfficientNet-B0):
gate MSP calibrated + ensemble disagreement trên raw logits — xem `docs/FLOW.md`.

Cấu trúc thư mục:

```
ml/
├── configs/
│   └── config.yaml          # Hyperparameter, đường dẫn, danh sách class
├── data/                    # gitignore — không push lên GitHub
│   ├── filtered/            # Bước 1: 38 class — data gốc từ HF
│   └── split/               # Bước 2: train/val/test
│       ├── train/<class>/
│       ├── val/<class>/
│       └── test/<class>/
├── src/
│   ├── download_dataset.py  # Bước 1: HF → file ảnh
│   ├── split_dataset.py     # Bước 2: chia train/val/test theo leaf_id
│   ├── data_loader.py       # Load ảnh từ disk + augment
│   ├── model.py             # build_model: mobilenet_v2 / resnet50 / efficientnet_b0
│   ├── train.py             # Bước 3: huấn luyện (suffix theo run_name)
│   ├── evaluate.py          # Đánh giá trên tập test
│   ├── calibration.py       # Temperature scaling
│   ├── ood_scoring.py       # MSP / Entropy / Energy / Ensemble disagreement + TIER_MODELS
│   ├── evaluate_ood.py      # Benchmark OOD + chốt ngưỡng per-tier
│   ├── predict.py           # Predictor inference 2 tầng (dùng chung cho BE tham khảo)
│   ├── gradcam.py           # Grad-CAM heatmap
│   ├── debug_gate.py        # Kiểm tra gate RAW vs CALIBRATED
│   └── compare_models.py    # So sánh model trên cùng ảnh
├── docs/
│   └── FLOW.md              # Flow hệ thống ML → BE → FE (bản commit)
├── models/                  # gitignore — best_model_*.pt, classes_*.json, temperature_*.json
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

Copy các bundle `<model>_f_v1/` (gồm `model.pt`, `classes.json`, `model_type.json`,
`temperature.json`, `manifest.json`) và `outputs/ood_threshold.json` vào
`backend/app/ml_assets/models/`. Backend verify manifest + sha256 + thứ tự class
trước khi seed (xem `backend/README.md`).

## Ghi chú

- `train.py` xuất file theo `train.run_name` trong `config.yaml` (mặc định theo `model_type`).
- `evaluate.py` / `calibration.py` luôn dùng `--model-suffix` để trỏ đúng model vừa train.
- Disagreement OOD luôn tính trên raw logits; gate MSP dùng calibrated (`--use-temperature`).
- Split chia theo **leaf_id** (leaf-map từ HF). Ảnh không có map dùng fallback 1 ảnh = 1 leaf.
