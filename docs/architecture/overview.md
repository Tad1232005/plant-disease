# Tổng quan kiến trúc

Hệ thống nhận diện bệnh lá cây (38 lớp PlantVillage) gồm 4 module độc lập trong cùng repo.

## Module và runtime

| Module | Stack | Chạy | Cổng |
|---|---|---|---|
| `ml/` | Python, PyTorch | `python src/train.py` (venv `ml/venv`) | — |
| `backend/` | FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, JWT | `uvicorn app.main:app --reload` | `:8000` (`/docs` Swagger) |
| `frontend/` | React 18, Vite 5, Tailwind, router v6 | `npm run dev` | `:5173` |
| `admin/` | React 18, router v7 (app riêng) | `npm run dev` | `:5174` |

PostgreSQL chạy ngoài source: `127.0.0.1:55432` (xem `backend/compose.postgres.yml`).
CORS backend cho phép `localhost:5173` và `5174`.

## Luồng dữ liệu end-to-end

```
Người dùng (FE :5173 / Admin :5174)
  │  POST /api/v1/predict (multipart: file, mode, strategy, model_type, farm_id?)
  ▼
Backend (:8000)
  ├─ validate_upload (MIME thật, dung lượng ≤ 10MB, pixel giới hạn)
  ├─ resolve_mode(role) → basic (guest) / standard (user, manager) / advanced (technician, admin)
  ├─ get_active_models(DB ModelVersion) → bundle trong app/ml_assets/models/
  ├─ predict_service.predict_bounded (cache model + temperature, soft-vote calibrated probs)
  │    checks: confidence ≥ 0.3, margin ≥ 0.05, JS divergence ≤ ngưỡng tier
  └─ complete_prediction → lưu Scan/ScanTopK/ScanModelResult (nếu đã đăng nhập)
  │  label + confidence + top_k + validation_status (accepted/low_confidence/ambiguous)
  ▼
FE hiển thị kết quả, lịch sử, Grad-CAM (POST/GET /scans/{id}/gradcam)
```

- Guest: không gửi `farm_id`, không lưu Scan.
- Auth: JWT access 15p + refresh 7 ngày (HttpOnly cookie); thu hồi bằng `token_version`.
- Chi tiết flow ML: `ml/docs/FLOW.md`. Contract OOD: `api/ood-contract.md`.

## Backend layered

`api/v1/endpoints/` → `services/` → `crud/` → `models/` (ORM) + `schemas/` (Pydantic).
Config tập trung `app/core/config.py` (pydantic-settings, đọc `.env`).
Xem bảng endpoint tại `api/endpoints.md`.
