# Contract OOD giữa ML và BE

> Quy tắc sắt: ai đổi contract ML↔BE phải bump version trong JSON để bên kia
> fail loudly thay vì sai âm thầm.

## Tín hiệu đã chốt: ensemble disagreement

Độ bất đồng giữa các backbone (KL trung bình so với mean probs). Disagreement cao → khả nghi OOD.
File single source of truth: `ml/outputs/ood_threshold.json` → copy sang
`backend/app/ml_assets/models/ood_threshold.json` (BE đọc từ đó).

## Tier và ngưỡng (percentile q=95 trên ID)

| Tier | Model | Ngưỡng trong JSON (**raw**) | Ngưỡng hiệu lực ở BE (**normalized**) |
|---|---|---|---|
| basic | EffNet-B0 (1) | MSP `0.933487` | MSP `0.933487` |
| standard | EffNet + MobileNet (2) | disagreement `0.021538` | `0.021538 / ln(2)` ≈ `0.031073` |
| advanced | EffNet + MobileNet + ResNet50 (3) | disagreement `0.035254` | `0.035254 / ln(3)` ≈ `0.032090` |

Gate MSP calibrated (`softmax(logits/T)`, `T≈1.49`): high `0.985229` (p90 ID), low `0.508453` (p1 ID).
FPR@OOD đo được: standard 4%, advanced 5%, basic 12%.

## Quy ước scale (bắt buộc)

- **`compute_ensemble_disagreement` (ML) tính trên raw logits, KHÔNG chia `ln(N)`.**
- **JSON lưu ngưỡng raw.** **`PredictService` (BE) chia `raw/ln(N)` khi đọc**
  (`_load_calibrated_thresholds`) và tính JS đã chuẩn hoá (`_js_divergence`).
- Hai bên phải khớp nhau: ML đổi sang normalized mà BE vẫn chia = double-normalize
  (ngưỡng sai ~1.4–2.4×). Hướng sửa đã thống nhất: canonical normalized +
  field `"score_scale": "js_normalized"` + version trong JSON, BE đọc theo scale
  (normalized dùng thẳng, raw mới chia). **Chưa code** — xem mục nợ kỹ thuật trong `AGENTS.md`.

## Ngưỡng `.env` và thứ tự ưu tiên (BE)

`get_js_divergence_threshold`: nếu `JS_DIVERGENCE_THRESHOLD` trong `.env` **khác**
default `0.035` → dùng env (bỏ qua JSON calibrate); nếu bằng → dùng ngưỡng tier từ JSON.
Giữ `.env` = `0.035`. Lịch sử: `.env` từng `0.3` khiến hệ thống chạy ngưỡng gấp ~10×.

## Rule quyết định ở BE (`predict`)

### 1. Phân nhánh Guest (Chỉ chạy Tầng 1 — `basic`):
- **Model**: `efficientnet_b0` duy nhất.
- **Ngưỡng kiểm tra**: Calibrated MSP `≥ 0.933487` (ngưỡng MSP calibrate q=95 ID trong `ood_threshold.json`) và `margin ≥ 0.05`.
- **Kết quả**:
  - Đạt cả 2: `is_valid_leaf = true`, `validation_status = "accepted"`, trả về nhãn bệnh.
  - Không đạt: `is_valid_leaf = false`, `label = null`, `validation_status = "low_confidence"` (hoặc OOD) → FE hiển thị cảnh báo **"Không phải lá"**.

### 2. Phân nhánh Role Đã Đăng Nhập (Cơ chế Cascade 2 Tầng):
- **Tầng 1 (Primary Model)**: Chạy model do người dùng chọn (mặc định EffNet-B0 nếu không chọn).
  - **Tầng 1 ổn (High Conf Gate)**: Calibrated MSP $\ge 0.985229$ (p90 ID) và $\text{margin} \ge 0.05$ $\rightarrow$ **Cho qua ngay (Early Exit)**, trả kết quả lập tức (`is_valid_leaf = true`, `validation_status = "accepted"`), **KHÔNG chạy Tầng 2** (chỉ tốn 1 forward pass, tối ưu độ trễ).
  - **Tầng 1 chắc chắn không phải lá (Low Conf Gate)**: Calibrated MSP $< 0.508453$ (p1 ID) $\rightarrow$ **Loại ngay từ Tầng 1 (Early Reject)**, `is_valid_leaf = false`, `label = null`, `validation_status = "low_confidence"`, **KHÔNG chạy Tầng 2**.
  - **Tầng 1 phân vân (Vùng lửng / nghi ngờ)**: $0.508453 \le \text{Calibrated MSP} < 0.985229$ (hoặc $\text{margin} < 0.05$) $\rightarrow$ **Bắt đầu kích hoạt Tầng 2**.
- **Tầng 2 (Auxiliary Models & Ensemble)**:
  - Chạy các model còn lại của Tier (Standard: thêm 1 model phụ; Advanced: thêm 2 model phụ).
  - Tổng hợp Soft-voting mean probabilities giữa các model và đo Jensen-Shannon (JS) Divergence.
  - **Kiểm định**:
    - `confidence ≥ 0.3` (soft-vote ensemble)
    - `top1_top2_margin ≥ 0.05`
    - `js_divergence ≤ ngưỡng tier` (Standard: `~0.031073`, Advanced: `~0.032090`)
  - Fail confidence → `low_confidence`, fail margin/js → `ambiguous`.
  - `ood_score = 0.4·(1−conf) + 0.3·entropy + 0.3·js` ghi nhận phục vụ audit/xếp hạng.
