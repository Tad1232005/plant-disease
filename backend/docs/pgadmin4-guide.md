# Sử dụng pgAdmin 4 Desktop

## Kết nối PostgreSQL local

Khởi động PostgreSQL trước:

```powershell
docker compose -f compose.postgres.yml up -d database
```

Trong pgAdmin 4 Desktop, nhấp phải **Servers**, chọn **Register > Server...**.

Tab **General**:

```text
Name: Plant Disease Local
```

Tab **Connection**:

```text
Host name/address: 127.0.0.1
Port: 55432
Maintenance database: plant_disease
Username: plant_app
Password: 123
Save password: On
```

Nếu có lựa chọn SSL mode, dùng `Prefer` cho local. Master Password của pgAdmin
chỉ bảo vệ mật khẩu đã lưu trên máy Windows; nó không phải mật khẩu PostgreSQL.

## Xem và sửa dữ liệu

Mở cây:

`Servers > Plant Disease Local > Databases > plant_disease > Schemas > public`

- Xem dữ liệu: `Tables > <tên bảng> > View/Edit Data > All Rows`.
- Chạy SQL: chọn `plant_disease`, sau đó mở **Tools > Query Tool**.
- Xem schema: mở `Columns`, `Constraints` và `Indexes` dưới từng bảng.

Ví dụ truy vấn chỉ đọc:

```sql
SELECT id, username, role, token_version
FROM users
ORDER BY id;

SELECT model_type, version_name, is_active, is_enabled
FROM model_versions
ORDER BY model_type, id;
```

## Sửa gì ở đâu?

| Muốn thay đổi | File hoặc nơi thực hiện |
| --- | --- |
| Host/port/user/password backend kết nối database | `.env` |
| Tên DB, user, password, cổng Docker local | `.env` |
| Cấu hình mẫu cho thành viên khác | `.env.example` |
| Image, port và volume PostgreSQL | `compose.postgres.yml` |
| Thêm/sửa cột, bảng, index, foreign key | `app/models/*.py`, sau đó tạo Alembic migration |
| Request/response và validation | `app/schemas/*.py` |
| Quyền và nghiệp vụ | `app/services/*.py` |
| HTTP route | `app/api/v1/endpoints/*.py` |
| Query của API | `app/crud/*.py` hoặc service tương ứng |
| Dữ liệu mặc định | `scripts/seed_week2.py` |
| Sửa một bản ghi local để kiểm thử | pgAdmin Query Tool |

Không dùng pgAdmin để tự tay thêm cột rồi bỏ qua Alembic. Thao tác đó chỉ đổi
database trên máy hiện tại và không thể tái tạo trên máy đồng đội/production.

Quy trình đổi schema:

```powershell
# Sửa ORM model trước, sau đó:
.\.venv\Scripts\python.exe -m alembic revision --autogenerate -m "mo ta thay doi"

# Đọc lại upgrade/downgrade trong file mới ở alembic/versions, rồi:
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic check
.\.venv\Scripts\python.exe -m pytest -q
```

## Sửa dữ liệu an toàn

Với một thay đổi thủ công, dùng transaction:

```sql
BEGIN;

UPDATE users
SET full_name = 'Tên mới'
WHERE username = 'normal_user';

SELECT id, username, full_name
FROM users
WHERE username = 'normal_user';

COMMIT;
-- Nếu kết quả sai, chạy ROLLBACK thay cho COMMIT.
```

Không sửa trực tiếp `password_hash`. Đổi role bằng script để tăng luôn
`token_version` và thu hồi JWT cũ:

```powershell
.\.venv\Scripts\python.exe -m scripts.update_role normal_user technician
```

## Đổi mật khẩu PostgreSQL

Đổi `POSTGRES_PASSWORD` trong `.env` không tự đổi mật khẩu của volume
đã tồn tại. Với database đang có dữ liệu, chạy trong Query Tool:

```sql
ALTER ROLE plant_app WITH PASSWORD 'mat_khau_moi_rat_manh';
```

Sau đó cập nhật `POSTGRES_PASSWORD` trong `.env` và connection đã lưu trong
pgAdmin. Nếu môi trường deploy có khai báo `DATABASE_URL` override thì cập nhật
cả URL đó. Không xóa volume chỉ để đổi password.

## Backup

Nhấp phải database `plant_disease`, chọn **Backup...**, format `Custom`. Khi
cần khôi phục, dùng **Restore...** trên database đích.

PostgreSQL lưu dữ liệu ở volume `plant_disease_postgres_data`. Không chạy
`docker compose down -v` nếu chưa chủ đích xóa toàn bộ dữ liệu.
