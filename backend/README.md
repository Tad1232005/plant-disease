# Backend Plant Disease API

FastAPI + SQLAlchemy + Alembic + SQLite. Phần Tuần 1-2 gồm Auth/JWT/RBAC,
6 bảng nền tảng, CRUD Farm và CRUD Disease Info.

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

Tài khoản seed local có mật khẩu mặc định `123321`: `admin_user`,
`manager_user`, `technician_user`, `normal_user`. Không dùng các tài khoản này
ở production. Có thể đặt biến `SEED_DEMO_PASSWORD` trước khi seed để đổi mật khẩu.

Seed còn tạo đủ 38 bản ghi `disease_info` khớp chính xác với
`app/ml_assets/classes.json` và một `model_version` demo nếu chưa có. Có thể
chạy lại lệnh seed nhiều lần; script chỉ thêm dữ liệu thiếu, không ghi đè dữ
liệu đã được chỉnh sửa.

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
- Farms: `/api/v1/farms`, `/api/v1/farms/{farm_id}`
- Disease Info: `/api/v1/disease-info`,
  `/api/v1/disease-info/{label_key}`

## Test

```powershell
# Test tích hợp không cần chạy server
.\.venv\Scripts\python.exe -m pytest -q

# Test trên server thật (chạy seed + uvicorn trước)
.\.venv\Scripts\python.exe scripts\smoke_week2.py
```

Hướng dẫn chi tiết và ma trận kết quả mong đợi nằm tại
[`docs/backend-guide.md`](docs/backend-guide.md).
