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
  │  POST /api/v1/predict (multipart: file, primary_model?, farm_id?)
  ▼
Backend (:8000)
  ├─ validate_upload (MIME thật, dung lượng ≤ 10MB, pixel giới hạn)
  ├─ resolve_mode(role) → basic (guest) / standard (user, manager) / advanced (technician, admin)
  │
  ├─ [Nhánh Guest]:
  │    └─ Dừng ở Tầng 1 (EfficientNet-B0): kiểm tra MSP calibrated ≥ 0.933487 và margin ≥ 0.05.
  │       Nếu không đạt ngưỡng %: is_valid_leaf = false, hiển thị "Không phải lá".
  │
  ├─ [Nhánh Role đã đăng nhập]:
  │    ├─ Nhận model do user chọn làm Primary Model (FE chỉ hiện chọn model, không chọn single/ensemble).
  │    └─ Bắt buộc chạy đủ 2 Tầng (Tầng 1: Primary Model + Tầng 2: các model phụ trợ trong tier).
  │       Tổng hợp soft-vote mean probs, kiểm tra checks: confidence ≥ 0.3, margin ≥ 0.05, JS ≤ ngưỡng tier.
  │
  └─ complete_prediction → lưu Scan/ScanTopK/ScanModelResult (nếu đã đăng nhập)
     label + confidence + top_k + validation_status (accepted/low_confidence/ambiguous)
  ▼
FE hiển thị kết quả chẩn đoán, cảnh báo "Không phải lá" (nếu fail), lịch sử, Grad-CAM.
```

- Guest: không chọn model, không gửi `farm_id`, không lưu Scan, dừng ở Tầng 1.
- Role đăng nhập: chọn model khả dụng theo role, bắt buộc chạy qua 2 tầng, lưu lịch sử Scan.
- Auth: JWT access 15p + refresh 7 ngày (HttpOnly cookie); thu hồi bằng `token_version`.
- Chi tiết flow ML: `ml/docs/FLOW.md`. Contract OOD: `api/ood-contract.md`.

## Backend layered

`api/v1/endpoints/` → `services/` → `crud/` → `models/` (ORM) + `schemas/` (Pydantic).
Config tập trung `app/core/config.py` (pydantic-settings, đọc `.env`).
Xem bảng endpoint tại `api/endpoints.md`.
