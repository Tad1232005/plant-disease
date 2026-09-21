# 1. Cài đặt và chạy backend local

## Yêu cầu

- Python 3.12.
- Docker Desktop đang chạy.
- Ba artifact model tại `app/ml_assets/models/*/model.pt`. JSON manifest đã có
  trong source nhưng trọng số lớn có thể không nằm trong Git.

## Khởi tạo

```powershell
cd C:\Project\plant-disease\backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
docker compose -f compose.postgres.yml up -d database
.\.venv\Scripts\python.exe -m scripts.check_database
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Không dùng `alembic downgrade` để rollback dữ liệu. Nếu migration production lỗi,
khôi phục snapshot đã backup thay vì hạ schema một cách mù quáng.

## Seed và chạy API

```powershell
# User demo + 38 Disease Info + đăng ký ba model version.
.\.venv\Scripts\python.exe -m scripts.seed_week2

# Tùy chọn: hai Farm demo, chỉ chạy ở development/test.
.\.venv\Scripts\python.exe -m scripts.seed_demo_farms

uvicorn app.main:app --reload
```

Mở Swagger: `http://127.0.0.1:8000/docs`. Tài khoản demo dùng mật khẩu
`Demo123321!`; đổi bằng `SEED_DEMO_PASSWORD` trước lần seed đầu tiên. Không dùng
tài khoản/seed demo ở production.

## Kiểm tra nhanh

```powershell
.\.venv\Scripts\python.exe -m scripts.preflight
.\.venv\Scripts\python.exe -m pytest -q tests/test_scans.py
```

`preflight` chỉ đọc DB/cấu hình, không tự migrate hoặc seed.
