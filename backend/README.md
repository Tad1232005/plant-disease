# Backend Plant Disease API

FastAPI + SQLAlchemy + Alembic + SQLite. Backend hiện gồm Auth/JWT/RBAC,
inference ensemble 1/2/3 model có persistence, CRUD Farm/Disease Info, Managed
User, Farm Members và lịch sử Scan theo owner.

## Chạy local

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
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

## Endpoint Tuần 4

- Admin Users: `POST/GET /api/v1/admin/users`
- Manager Users: `POST/GET /api/v1/manager/users`
- Farm Members: `POST/GET /api/v1/farms/{farm_id}/members`,
  `DELETE /api/v1/farms/{farm_id}/members/{user_id}`
- Scans: `GET /api/v1/scans/history`, `GET/DELETE /api/v1/scans/{scan_id}`

## Test

```powershell
# Test tích hợp không cần chạy server
.\.venv\Scripts\python.exe -m pytest -q

# Test trên server thật (chạy seed + uvicorn trước)
.\.venv\Scripts\python.exe scripts\smoke_week2.py
```

Hướng dẫn chi tiết và ma trận kết quả mong đợi nằm tại
[`docs/backend-guide.md`](docs/backend-guide.md) và
[`docs/week3-guide.md`](docs/week3-guide.md),
[`docs/week4-guide.md`](docs/week4-guide.md).
