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

`confidence ≥ 0.3` và `margin ≥ 0.05` và `js_divergence ≤ ngưỡng tier`,
fail confidence → `low_confidence`, fail còn lại → `ambiguous`.
`ood_score = 0.4·(1−conf) + 0.3·entropy + 0.3·js` chỉ để log/xếp hạng.
