# AGENTS.md — Single source of truth cho AI agent

## 1. Tổng quan
- Đồ án Quản lý phần mềm (3 người): nhận diện bệnh lá cây từ ảnh + confidence score.
- 4 module: `ml/` train/eval (PyTorch, venv `ml/venv`); `backend/` REST API (FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, JWT, `:8000`); `frontend/` web user (React 18, Vite 5, Tailwind, router v6, `:5173`); `admin/` web quản trị app riêng (React 18, router v7, `:5174`).
- Flow hệ thống: `ml/docs/FLOW.md`. Log thực nghiệm ML: `ml/FLOW.local.md` (local, không commit).
- Tài liệu: `docs/` (`architecture/overview.md`, `architecture/api/endpoints.md`, `architecture/api/ood-contract.md`, `project/roles.md`).

## 2. Backend (`backend/`)
- Entry `app/main.py`, prefix `/api/v1` (`/docs` Swagger): `auth`, `predict`, `scans`, `farms`, `disease-info`, `proposals`, `stats`, `model-versions`.
- Layered: `api/v1/` → `services/` → `crud/` → `models/`; config `core/config.py` (pydantic-settings, `.env`).
- DB models: `User`, `Farm`, `FarmMember`, `DiseaseInfo`, `DiseaseProposal`, `Scan`, `ScanTopK`, `ScanModelResult`, `ModelVersion`, `AuthRateLimit`, `AuditEvent`. Migrations bằng Alembic (`alembic/versions/`).
- Model artifacts: `app/ml_assets/models/` (bundle `<model>_f_v1/` + `ood_threshold.json`), verify qua `manifest.json` + sha256 (`model_artifact_service.py`).
- OOD: default `JS=0.035`; `PredictService` đọc ngưỡng per-tier từ `ood_threshold.json` rồi chuẩn hoá `raw/ln(N)` → hiệu lực `~0.031` (standard) / `~0.032` (advanced). `.env` phải bằng default, nếu khác thì ngưỡng calibrate bị bỏ qua (`get_js_divergence_threshold` ưu tiên env override). Checks: confidence≥0.3, margin≥0.05, JS≤ngưỡng tier.
- Bẫy: `app/routes/predict.py` + `app/schemas.py` là di tích (thật: `app/api/v1/`, package `app/schemas/`).
- Tests: pytest cần PostgreSQL `127.0.0.1:55432` (cả unit test cũng dính fixture DB).
- CI (`.github/workflows/ci.yml`, chạy trên PR vào `dev`/`main`): `backend-test` (pytest + Postgres service), `frontend-build`, `admin-build`. Add 3 checks này vào required checks của ruleset `dev` + `main`. ML không chạy CI.

## 3. ML (`ml/`)
- `download_dataset.py` → `data/filtered/` (38 class) → `split_dataset.py` → `data/split/` (70/15/15, seed 42, leaf_id) → `train.py` → `models/` (suffix `_f`) → `calibration.py` → `evaluate_ood.py` → `outputs/ood_threshold.json`.
- Disagreement trên raw logits; JSON lưu ngưỡng raw; đổi contract ML↔BE thì bump version trong JSON.
- `data/`, `models/`, `*.log` không commit.

## 4. Frontend (`frontend/`) & Admin (`admin/`)
- `frontend/`: `/`, `/login`, `/register`, `/app/{dashboard,scan,history,farms,diseases}`.
- `admin/`: `/admin/{dashboard,users,farms,diseases,proposals,models,system}`; services gọi API thật, không fallback.
- Roles `user|technician|manager|admin`; JWT qua `utils/storage.js`; CORS `5173/5174`.

## 5. Git
- Nhánh tính năng: `feature/*` (rẽ từ `dev`). Không push trực tiếp `dev`/`main`.
- Flow: `feature/*` → PR vào `dev` (Leader review) → `dev` ổn định → PR vào `main`.
- Trước khi code: pull `dev` mới nhất; xử lý conflict trước khi tạo PR.
- Commit tiếng Việt không dấu, conventional (`feat:`, `fix:`). Không commit dữ liệu/model.

## 6. Làm việc
- Đọc file liên quan, lập plan, xác nhận trước khi code. Giữ convention sẵn có.
- Không tạo `*.md` nếu không yêu cầu. Sửa xong tự review + chạy test/lint khi khả thi.

## 7. Nợ kỹ thuật đang mở
- OOD contract còn ngầm: ML lưu ngưỡng raw, BE tự chia `ln(N)` bù; `compute_ensemble_disagreement` chưa có param `normalize`; JSON thiếu `score_scale`/`version` (hướng sửa đã thống nhất: canonical normalized + version để fail loudly, chưa code).
- `.env` từng `JS=0.3` làm ngơ ngưỡng calibrate — đã sửa về `0.035`.
- pytest phụ thuộc Postgres ngoài, chưa có docker/testcontainers.
- Theo plan 8 tuần: camera capture, dashboard farm, báo cáo/bảo vệ chưa làm.
- Phân quyền chưa xong: admin chưa xem được farms, manager chưa xem được history của managed user (chi tiết trong `docs/project/roles.md`).
