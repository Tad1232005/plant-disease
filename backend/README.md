# Backend Plant Disease API

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