# Flow ML — Plant Disease Detection (local, không push GitHub)

Nguyên tắc: **tải 1 lần → export file → các bước sau chỉ đọc file**, không gọi Hugging Face lúc train.

---

## Pipeline tổng quan

```
[Bước 0] Setup venv + pip install                                          ✅
[Bước 1] download_dataset.py  →  data/filtered/      (38 class, ~54k ảnh)  ✅
[Bước 2] split_dataset.py     →  data/split/         (leaf split 70/15/15) ✅
[Bước 3] train.py             →  models/             (best_model.pt)       ✅ Colab GPU
[Bước 4] evaluate.py          →  outputs/            (metrics + figures)   ✅
[Bước 5] copy model           →  backend/app/models/                       ✅
[Bước 6] predict.py           →  inference module                           ✅
[Bước ?] gradcam / calibration / EDA                                        ⏳
```

---

## Bước 0 — Setup (1 lần)

```powershell
cd D:\QLPM\plant-disease-detection\ml
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Kiểm tra venv: đầu dòng lệnh có `(venv)`. Dùng `python -m pip` nếu lệnh `pip` không nhận.

---

## Bước 1 — Download ✅

### Mục tiêu

Tải PlantVillage, export ảnh RGB vào `data/filtered/` làm **data gốc** cho cả nhóm.

### Dataset

- Repo: https://huggingface.co/datasets/mohanty/PlantVillage
- Ảnh thật trong **`data.zip`** (~2GB)
- Script chỉ lấy **`raw/color/`** (~54k ảnh, 38 class) — bỏ grayscale/segmented

### Chạy lệnh

```powershell
cd D:\QLPM\plant-disease-detection\ml
.\venv\Scripts\Activate.ps1
py src/download_dataset.py
```

### Script làm gì?

1. Tải `data.zip` qua Hugging Face (cache: `C:\Users\<user>\.cache\huggingface\`)
2. Giải nén path `raw/color/*` → `data/filtered/<class>/`
3. Chạy lại an toàn — file đã có thì bỏ qua

### Output

```
ml/data/filtered/
├── Tomato___healthy/
├── Apple___Black_rot/
└── ... (38 thư mục class, ~54,305 ảnh)
```

### Lưu ý

- Không push `data/filtered/` lên GitHub
- Chia sẻ nhóm: nén folder → Google Drive, giải nén vào `ml/data/filtered/`

### Lỗi thường gặp

| Lỗi | Cách xử lý |
|---|---|
| `pip not recognized` | `python -m pip install ...` trong venv |
| `BuilderConfig 'color' not found` | Đã sửa — dùng data.zip |
| `KeyError: 'label'` | Đã sửa — extract từ zip, không load_dataset |

---

## Bước 2 — Split theo leaf ✅

### Chạy lệnh

```powershell
$env:PYTHONIOENCODING='utf-8'
py src/split_dataset.py
```

### Script làm gì?

1. Tự tải `leaf-map.json` từ HF → `data/metadata/` (gitignore)
2. Lọc class theo `target_classes` trong `configs/config.yaml` (hiện: **38 class**)
3. Gom ảnh **cùng lá** (leaf_id) — không tách train/val/test
4. Chia leaf: **70% train / 15% val / 15% test** (stratified theo class)
5. Copy ảnh → `data/split/{train,val,test}/<class>/`

### Kết quả đã chạy

| Tập | Số ảnh |
|---|---|
| train | 37,996 |
| val | 8,135 |
| test | 8,174 |

- Leaf có map: 40,296 | fallback solo (1 ảnh/leaf): 11,708

### Đổi scope class

Sửa `target_classes` trong `config.yaml` → chạy lại `split_dataset.py`.  
`data/filtered/` vẫn giữ 38 class làm data gốc.

---

## Bước 3 — Train ✅ (Colab GPU)

**Scope:** giữ **38 class**. Train trên **Google Colab T4** (laptop AMD iGPU → PyTorch chỉ CPU, quá chậm).

### Local (nếu có NVIDIA GPU)

```powershell
cd D:\QLPM\plant-disease-detection\ml
.\venv\Scripts\Activate.ps1
$env:PYTHONIOENCODING='utf-8'
py src/train.py
```

### Input

| Nguồn | Vai trò |
|---|---|
| `data/split/train/` | Học weights |
| `data/split/val/` | Chọn epoch tốt nhất (`best_model.pt`) |
| `configs/config.yaml` → `train:` | Hyperparameter |

**Không** dùng `data/split/test/` lúc train — test chỉ cho evaluate.

### Output

- `models/best_model.pt` (~9 MB) — epoch có **val_acc** cao nhất
- `models/classes.json` — 38 tên class theo index (backend predict)

### Hyperparameter mặc định

| Key | Giá trị |
|---|---|
| batch_size | 32 |
| epochs | 15 |
| lr | 0.0001 |
| image_size | 224 |

### Kết quả đã train

- MobileNetV2, 38 class, ~2.27M params
- Copy từ Colab Drive → `ml/models/best_model.pt` + `classes.json`

### Colab

Xem `notebooks/train_colab.ipynb` và **Phụ lục Colab** cuối file.

---

## Bước 4 — Evaluate ✅

```powershell
cd D:\QLPM\plant-disease-detection\ml
.\venv\Scripts\Activate.ps1
$env:PYTHONIOENCODING='utf-8'
py src/evaluate.py
```

### Input

| Nguồn | Vai trò |
|---|---|
| `data/split/test/` | 8,174 ảnh — **chỉ dùng 1 lần** sau train |
| `models/best_model.pt` | Weights đã train |
| `models/classes.json` | Map index ↔ tên class |

### Script làm gì?

1. Load model + infer toàn bộ test set (256 batch × batch_size 32)
2. In **Test Accuracy** + **Classification Report** (precision / recall / F1 / support)
3. Lưu metrics + vẽ 2 confusion matrix

Terminal có **progress bar** `Evaluating: xx/256` — không treo, chỉ chậm trên CPU.

### Output

| File | Nội dung | Push GitHub? |
|---|---|---|
| `outputs/metrics.json` | Accuracy, macro/weighted avg, 38 class (C01–C38) | **Có** (~10 KB) |
| `outputs/figures/confusion_matrix.png` | Ma trận đầy đủ — trục C01–C38, màu theo số ảnh | **Có** |
| `outputs/figures/confusion_matrix_errors.png` | Chỉ ô predict **sai** (ẩn đường chéo), có số | **Có** |

### Kết quả đã chạy (2026-08-13)

| Metric | Giá trị |
|---|---|
| Test accuracy | **99.80%** |
| Test samples | 8,174 |
| Macro F1 | 99.73% |
| Weighted F1 | 99.80% |

### Đọc confusion matrix

- **`confusion_matrix.png`**: Actual (dọc) vs Predicted (ngang). Đường chéo = đúng; ngoài chéo = nhầm. Tra class: `metrics.json` → `per_class[].code` / `name`.
- **`confusion_matrix_errors.png`**: Chỉ lỗi — với 99.8% accuracy chỉ vài ô đỏ nhỏ.

### Thời gian

| Môi trường | ~Thời gian |
|---|---|
| CPU (laptop AMD, PyTorch +cpu) | **6–7 phút** |
| Colab GPU | ~30 giây–1 phút |

### Cấu trúc `metrics.json`

```json
{
  "accuracy": 0.998043,
  "test_samples": 8174,
  "macro_avg": { "precision", "recall", "f1_score" },
  "weighted_avg": { ... },
  "per_class": [
    { "code": "C01", "name": "Apple___Apple_scab", "precision", "recall", "f1_score", "support" }
  ]
}
```

---

## Bước 5 — Đưa model sang backend ✅

Copy vào `backend/app/models/`:

- `models/best_model.pt`
- `models/classes.json`

Đã thêm vào `backend/.gitignore` để không push model lên GitHub.

---

## Bước 6 — Module inference (predict.py) ✅

### Chạy lệnh

```powershell
cd D:\QLPM\plant-disease-detection\ml
.\venv\Scripts\Activate.ps1
py src/predict.py --image "data\split\test\Apple___Cedar_apple_rust\fc477749-2fe6-48a5-9393-5eedeb7cedc3___FREC_C.Rust 3826.JPG"
```

### Script làm gì?

1. Load model (`best_model.pt`) + classes (`classes.json`)
2. Preprocess ảnh PIL → tensor (resize 224x224, normalize)
3. Predict → trả `{label, confidence, all_probs}`
4. CLI test: in kết quả + top 5 probabilities

### Output format

```python
{
  "label": "Tomato___healthy",
  "confidence": 0.9876,
  "all_probs": [0.001, 0.002, ..., 0.9876, ...]  # 38 values
}
```

### Kết quả đã test

- Test với ảnh → predict đúng, confidence 100%
- Module inference sẵn sàng dùng chung cho ML và backend

### Dùng trong Python

```python
from ml.src.predict import load_predictor
from PIL import Image

predictor = load_predictor()
result = predictor.predict_single(image)
```

---

## Push GitHub — file nào?

| Push | Không push |
|---|---|
| `ml/outputs/metrics.json` | `ml/data/` |
| `ml/outputs/figures/confusion_matrix*.png` | `ml/models/*.pt` |
| Code `ml/src/`, `configs/`, `notebooks/` | `ml/FLOW.local.md` |

**`.gitkeep`**: placeholder để Git track thư mục rỗng (`outputs/figures/`, `outputs/logs/`).

---

## EDA / còn thiếu (làm sau)

| Task | Trạng thái |
|---|---|
| `notebooks/train_colab.ipynb` | ✅ |
| EDA notebook | ⏳ |
| `ml/src/predict.py` | ✅ |
| `gradcam.py` | ⏳ |
| `calibration.py` | ⏳ |

---

## Config quan trọng (`configs/config.yaml`)

| Key | Vai trò |
|---|---|
| `paths.filtered_dir` | Data gốc 38 class |
| `paths.split_dir` | Train/val/test sau split |
| `paths.metadata_dir` | leaf-map.json |
| `target_classes` | Class đưa vào split (38) |
| `split.*` | Tỷ lệ train/val/test theo leaf |
| `train.*` | batch, epochs, lr, image_size |
| `huggingface.variant` | `color` = raw/color/ từ zip |

---

## Lệnh nhanh

```powershell
cd D:\QLPM\plant-disease-detection\ml
.\venv\Scripts\Activate.ps1
$env:PYTHONIOENCODING='utf-8'

# Evaluate (sau khi có best_model.pt)
py src/evaluate.py

# Train local (cần NVIDIA GPU; không thì dùng Colab)
py src/train.py
```

---

*Cập nhật: 2026-08-14 — Download + split + train (Colab) + evaluate + copy model sang backend + predict.py xong. Module inference sẵn sàng dùng chung cho ML và backend.*

---

## Phụ lục — Google Colab (train bằng GPU)

### Chuẩn bị trên máy (1 lần)

```powershell
# Trong ml/ — nén data split (bắt buộc)
Compress-Archive -Path data\split -DestinationPath split.zip

# Tuỳ chọn: nén code (nếu chưa push GitHub)
# Bỏ venv, data/filtered — chỉ cần src/, configs/, requirements.txt
```

Upload lên Google Drive, ví dụ: `My Drive/Project_plant_disease/data/split.zip`

### Trên Colab

1. Vào https://colab.research.google.com/
2. **File → Upload notebook** → chọn `ml/notebooks/train_colab.ipynb`
3. **Runtime → Change runtime type → T4 GPU**
4. Sửa đường dẫn Drive trong notebook (`Project_plant_disease/...`)
5. **`USE_GIT = False`** + upload `ml_code.zip` nếu clone GitHub lỗi
6. **Runtime → Run all** (hoặc chạy từng cell)
7. **Chạy cell copy model lên Drive** trước khi đóng session

### Sau khi train xong

- Notebook copy `best_model.pt` + `classes.json` lên Drive
- Tải về máy → copy vào `ml/models/`
- Chạy `py src/evaluate.py` trên máy local (CPU ~6 phút) hoặc evaluate trên Colab nếu muốn nhanh

### Tắt máy local được không?

- **Colab:** train chạy trên server Google — máy bạn tắt được
- **Lưu ý:** session free ~12h, idle lâu có thể ngắt — giữ tab hoặc copy model lên Drive sớm
- **Local `py src/train.py` / `py src/evaluate.py`:** tắt/sleep máy → process **dừng ngay**
- **Laptop AMD iGPU:** PyTorch cài bản `+cpu` — không dùng GPU local được; train/eval nhanh → Colab
