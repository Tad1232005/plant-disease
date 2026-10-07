# FLOW hệ thống — ML + ML → BE → FE (bản commit, ngắn gọn)

> Chi tiết thực nghiệm dài nằm ở `ml/FLOW.local.md` (local, không push).
> File này là bản tóm tắt được commit: pipeline ML, artifacts bàn giao, và flow end-to-end.

## 1. Pipeline ML (file-based, không gọi HF lúc train)

```
download_dataset.py → data/filtered/   (38 class PlantVillage, ~54k ảnh)
split_dataset.py    → data/split/      (70/15/15 theo leaf_id, seed 42)
train.py            → models/          (best_model_<suffix>.pt + classes_<suffix>.json)
calibration.py      → models/temperature_<suffix>.json   (T cho ID calibration)
evaluate.py         → outputs/figures/ (metrics, confusion matrix)
evaluate_ood.py     → outputs/ood_threshold.json         (ngưỡng OOD, single source of truth)
```

Suffix đã train: `_f` (`efficientnet_b0_f`, `mobilenet_v2_f`, `resnet50_f`).
Không trộn logits `best_model.pt` cũ vào ensemble (thứ tự classes khác).

## 2. OOD gating theo tier (logic ML)

| Tier | Model | Tín hiệu |
|---|---|---|
| basic | EffNet-B0 | 1 ngưỡng MSP |
| standard | EffNet + MobileNet | MSP gate + disagreement 2-model |
| advanced | EffNet + MobileNet + ResNet50 | MSP gate + disagreement 3-model |

- Primary mọi tier: EfficientNet-B0. `disagreement` bất biến theo tập model nên đổi primary không cần calibrate lại.
- Gate MSP chạy trên **calibrated MSP** `softmax(logits/T)` (`--use-temperature`); disagreement luôn trên **raw logits**.
- Ngưỡng chốt `q=95` trên ID (`outputs/ood_threshold.json`): standard raw `0.021538`, advanced raw `0.035254`.
- Lưu ý scale: JSON hiện lưu **raw** (chưa `normalize`); BE chia `ln(N)` khi đọc → hiệu lực `~0.031/0.032` (`predict_service.py:_load_calibrated_thresholds`). Kế hoạch chuẩn hoá canonical + `score_scale`/`version` đã thống nhất riêng.

## 3. Artifacts ML → BE

Copy sang `backend/app/ml_assets/models/`:

```
<model>_f_v1/{model.pt, classes.json, model_type.json, temperature.json, manifest.json}
ood_threshold.json
```

BE verify bundle qua `manifest.json` + sha256 (`model_artifact_service.py`); `classes` 3 model phải cùng thứ tự.

## 4. Flow end-to-end ML → BE → FE

```
FE (React)                          BE (FastAPI, prefix /api/v1)              ML artifacts
──────────                          ────────────────────────────              ─────────────
ScanPage upload ảnh ──POST /predict (multipart, mode/strategy)──→ validate_upload (MIME, size)
  │                                     resolve_mode(role) → basic/standard/advanced
  │                                     get_active_models(DB ModelVersion)
  │                                     predict_service.predict_bounded ──> load .pt + T scaling
  │                                       soft-vote mean probs → confidence / margin / entropy / JS (normalized)
  │                                       checks: confidence, margin, model_disagreement_too_high
  │                                       ood_score = 0.4(1-conf)+0.3 entropy+0.3 JS
  │                                     complete_prediction → lưu Scan/ScanTopK (nếu login)
  └── label/confidence/top_k ←────── PredictResponse (validation_status, rejection_reason, agreement_status)
GET /scans/history, /scans/{id}, POST /scans/{id}/gradcam (giải thích, không quyết định)
GET /predict/capabilities → FE biết mode/strategy được phép theo role
```

## 5. Lệnh chạy nhanh

```powershell
# ML train/eval/OOD
cd ml; .\venv\Scripts\Activate.ps1
python src/train.py
python src/evaluate_ood.py --tier standard --ood-dir data/ood_test/near_ood --max-id-images 2000 --use-temperature
python src/predict.py --image "path/to/leaf.jpg" --tier standard

# BE / FE
cd backend; uvicorn app.main:app --reload      # :8000, Swagger /docs
cd frontend; npm run dev                        # :5173
```
