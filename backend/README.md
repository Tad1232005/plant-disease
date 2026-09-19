# Backend Plant Disease API

[Mục lục tài liệu](docs/README.md) · [Hướng dẫn triển khai](docs/week8/DEPLOYMENT.md)

## Hiện tại: backend `1.1.0-rc.2`

Schema cần `d0e1f2a3b4c5` (thêm bảng vận hành `auth_rate_limits`).
[Báo cáo và cách test bổ sung](docs/week8/NON_ML_COMPLETION.md).
Auth thêm HTTP 429/Retry-After; X-Request-ID và JSON access log không chứa query/body.
Script đổi role mặc định dry-run, bắt buộc lý do và `--apply` khi muốn ghi.
Chưa coi DB ứng dụng đã nâng chỉ vì code/test đã có migration.

## Bổ sung vận hành tuần 8 — không thay đổi model

[Hướng dẫn triển khai/kiểm tra](docs/week8/DEPLOYMENT.md) ·
[Báo cáo thay đổi](docs/week8/REPORT.md).

- `python -m scripts.preflight`: chỉ đọc cấu hình/DB/schema/thư mục ảnh, không migrate.
- `python -m scripts.bootstrap_admin --username <ten-admin> --confirm-create`:
  tạo Admin đầu tiên qua terminal sau migration, không cần seed demo/model.
- `APP_ENV=production` bật kiểm tra secret, HTTPS origins và Secure Cookie;
  chặn seed demo. Khai báo `PUBLIC_API_ORIGIN` đúng origin API, không có dấu `/` cuối.
- `compose.backend.yml` chạy API CPU-only bằng user không root, DB quản lý riêng.
  Không tự migrate/seed; volume ảnh container là kho riêng, không tự nhập ảnh local.


## Mốc tuần 7 trước đó — phần backend không ML

Contract API `1.1.0-rc.1`, schema `c9d0e1f2a3b4`.
[Báo cáo/cách kiểm thử và backup](docs/week7/REPORT.md) ·
[Handoff FE](docs/week7/FRONTEND_HANDOFF.md) · [OpenAPI](docs/week7/openapi.json).
Thêm `/health/live` và `/health/ready` (readiness chỉ DB/schema, không model).
Chưa migrate DB ứng dụng hoặc nghiệm thu frontend/production.

FastAPI + SQLAlchemy + Alembic + PostgreSQL.
Backend hiện gồm Auth/JWT/RBAC,
inference ensemble 1/2/3 model có persistence, CRUD Farm/Disease Info, Managed
User, Farm Members và lịch sử Scan theo owner.

## Chạy local

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
docker compose -f compose.postgres.yml up -d database
python -m scripts.check_database
alembic upgrade head
python -m scripts.seed_week2
uvicorn app.main:app --reload
```

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

Tài khoản seed local có mật khẩu mặc định `Demo123321!`: `admin_user`,
`manager_user`, `technician_user`, `normal_user`. Không dùng các tài khoản này
ở production. Có thể đặt biến `SEED_DEMO_PASSWORD` trước khi seed để đổi mật khẩu.

Seed còn tạo đủ 38 bản ghi `disease_info` và đăng ký ba version active độc lập:
EfficientNet-B0, MobileNetV2 và ResNet50. Trước khi ghi DB, script xác minh
manifest, task, input size, thứ tự class, temperature và SHA-256 của bundle. Có thể
chạy lại lệnh seed nhiều lần; script chỉ thêm dữ liệu thiếu, không ghi đè dữ
liệu đã được chỉnh sửa.

Các file `*.pt` lớn được Git ignore. Mỗi môi trường triển khai phải đặt đủ ba
`model.pt` đúng thư mục artifact trước khi chạy seed; các JSON manifest/classes/
temperature được version-control để backend kiểm tra contract.

Logout thu hồi ngay cả access và refresh token bằng `token_version`. Farm và
Disease Info dùng soft-delete (`archived_at`/`is_active`) để không làm mất dữ
liệu phục vụ lịch sử Scan và dashboard.

## Cấu trúc thư mục

```text
app/
├── api/v1/endpoints/  # HTTP endpoint theo version
├── core/              # cấu hình, JWT, password hashing
├── crud/              # truy vấn dữ liệu thuần
├── db/                # engine, session, SQLAlchemy Base
├── models/            # ORM models và constraints
├── schemas/           # Pydantic request/response schemas
├── services/          # business logic
└── main.py            # khởi tạo FastAPI
alembic/               # migration database
scripts/               # seed và smoke test chạy thủ công
tests/                 # test tích hợp tự động
docs/                  # tài liệu kỹ thuật
```

## Endpoint Tuần 1-2

- Auth: `/api/v1/auth/register`, `/login`, `/refresh`, `/logout`, `/me`
- Farms (Manager sở hữu): `POST/GET /api/v1/farms`,
  `GET/PUT/DELETE /api/v1/farms/{farm_id}`
- Disease Info: `/api/v1/disease-info`,
  `/api/v1/disease-info/{label_key}`

## Endpoint Tuần 3

- Predict: `POST /api/v1/predict` dạng multipart với `file`, `farm_id` và
  `mode=auto|basic|standard|advanced` tùy chọn. Guest mặc định Basic (1 model),
  User/Manager Standard (2), Technician/Admin Advanced (3). Server luôn chặn
  mode vượt quyền. `GET /api/v1/predict/capabilities` cung cấp contract cho FE.

### Hiệu chỉnh tuần 3 — 08/09/2026

#### Bổ sung chọn model và giải thích quyết định

`POST /api/v1/predict` giữ nguyên mặc định ensemble, bổ sung multipart:

- `strategy=single` + `model_type=efficientnet_b0|mobilenet_v2|resnet50` để chỉ
  chạy một model; dùng `mode=auto` hoặc một mode cho phép model đó.
- `strategy=ensemble` (mặc định) không nhận `model_type`; chạy các model của mode.
- Guest: EfficientNet; User/Manager: EfficientNet hoặc MobileNet;
  Technician/Admin: cả ba. Chọn vượt quyền/mode nhận 403; tham số mâu thuẫn 422;
  model được chọn không active/enabled nhận 503, không tự đổi sang model khác.
- Response có `inference_strategy`, `selected_model_type`, `decision_details`
  (các giá trị/ngưỡng thực dùng và mọi rule thất bại). `inference_mode` là tier
  được resolve, không còn dùng để suy ra số model chạy; đọc `models_requested`.
- Policy mới: `ensemble-rgb224-v3-selection`; không đổi ngưỡng hoặc xác suất
  ensemble. `model_results[].accepted` kiểm cả confidence và margin của model.
- Scan detail có `prediction_context`; dữ liệu cũ giữ null. Migration mới
  `b8c9d0e1f2a3`, nối sau `a7b8c9d0e1f2` đã khôi phục. Cần `alembic upgrade head`
  trước deploy; DB local đã được nâng cấp và giữ nguyên 9 Scan hiện có.

Xem [báo cáo test ảnh tải từ Internet và hướng dẫn dùng](docs/predict-selection-audit/REPORT.md).

- Preprocessing: RGB → resize trực tiếp 224×224 bilinear/antialias → ToTensor →
  ImageNet normalization, không center crop. Bản đầu dùng policy `ensemble-rgb224-v2`;
  bản chọn model ở trên dùng `ensemble-rgb224-v3-selection`.
- `is_valid_leaf` giữ để tương thích nhưng deprecated: nó chỉ phản ánh policy
  accepted, không xác nhận ảnh là lá. Predict và capabilities bổ sung
  `input_assessment.leaf_detection_status=not_performed` và
  `quality_status=not_assessed`. Chưa có detector lá hay bộ đánh giá độ mờ/tối.
- Trạng thái từ chối không trả label kết luận hoặc nội dung điều trị. Top-k vẫn
  giữ để audit, không phải chẩn đoán. Accepted cũng có warning về giới hạn.
- Giữ ngưỡng 0.3; không tự nâng ngưỡng hoặc gọi temperature scaling là OOD.
- Công cụ offline dùng ba model thật, không ghi DB/train/sửa artifact:

```powershell
.\.venv\Scripts\python.exe -m scripts.evaluate_input_policy --synthetic --output docs/week3-rescue/my-synthetic-run.json
```

Output phải là file mới trong backend, không ghi đè. Hướng dẫn manifest ảnh thật,
ảnh hưởng API và kết quả kiểm thử: [báo cáo tuần 3](docs/week3-rescue/REPORT.md).

## Endpoint Tuần 4

- Admin Users: `POST/GET /api/v1/admin/users`
- Manager Users: `POST/GET /api/v1/manager/users`
- Farm Members: `POST/GET /api/v1/farms/{farm_id}/members`,
  `DELETE /api/v1/farms/{farm_id}/members/{user_id}`
- Scans: `GET /api/v1/scans/history`, `GET/DELETE /api/v1/scans/{scan_id}`

## Test

```powershell
# Test tích hợp trên database PostgreSQL riêng `plant_disease_test`.
# PostgreSQL container phải đang chạy; test tự tạo và xóa database test.
.\.venv\Scripts\python.exe -m pytest -q

# Test trên server thật (chạy seed + uvicorn trước)
.\.venv\Scripts\python.exe scripts\smoke_week2.py
```

# Cập nhật backend không phụ thuộc ML (15/09/2026)

Đã bổ sung `/api/v1/auth/change-password`, `/api/v1/me/farms` và
`/api/v1/scans/{scan_id}/image`; siết null/field ngoài schema cho Farm và
Disease Info; phân trang hai danh sách này (50 mặc định, tối đa 100).
Xem [hợp đồng, cách test và giới hạn kiểm chứng](docs/non-ml-tasks-20260915.md).
Lượt tiếp tục đã kiểm thử các luồng này trên PostgreSQL tạm, độc lập DB ứng dụng.

## Tuần 5–6: tài khoản, giám sát và duyệt nội dung (không ML)

Đã bổ sung status User/audit, Farm và Admin stats, Admin scans/ảnh riêng,
Disease Proposals có revision và duyệt/từ chối nguyên tử. Danh sách account và
Farm Members cũng có phân trang 50/100. Tổng cộng 41 thao tác API nghiệp vụ.
Xem [hợp đồng API, migration, cách test và phạm vi hoãn](docs/week5-week6-non-ml.md).

**Code mới cần migration `c9d0e1f2a3b4`**. Backup DB, xác nhận cấu hình, chạy
`python -m alembic upgrade head` trước khi restart API. Lượt này chỉ migrate DB
test, chưa nâng schema DB ứng dụng. Không dùng downgrade trên DB có dữ liệu.
