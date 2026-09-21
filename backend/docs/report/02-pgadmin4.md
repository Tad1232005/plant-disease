# 2. Kết nối pgAdmin 4

Khởi động Docker PostgreSQL trước:

```powershell
docker compose -f compose.postgres.yml up -d database
```

Trong pgAdmin 4: **Servers → Register → Server**.

| Tab | Trường | Giá trị local mặc định |
| --- | --- | --- |
| General | Name | `Plant Disease Local` |
| Connection | Host name/address | `127.0.0.1` |
| Connection | Port | `55432` |
| Connection | Maintenance database | `plant_disease` |
| Connection | Username | `plant_app` |
| Connection | Password | đọc từ `POSTGRES_PASSWORD` trong `.env` |
| Connection | Save password | chỉ bật trên máy cá nhân |
| SSL | SSL mode | `Prefer` cho local |

Master Password của pgAdmin chỉ bảo vệ mật khẩu đã lưu trên máy; nó không phải
mật khẩu PostgreSQL.

Sau khi kết nối: `Databases → plant_disease → Schemas → public → Tables`.
Không tạo/sửa cột thủ công trong pgAdmin; thay đổi schema phải qua ORM và Alembic.

Ví dụ truy vấn chỉ đọc:

```sql
SELECT id, username, role, status FROM users ORDER BY id;
SELECT label_key, disease_name, severity_level FROM disease_info ORDER BY label_key;
SELECT model_type, version_name, is_active, is_enabled FROM model_versions ORDER BY model_type;
SELECT id, name, user_id AS owner_id, archived_at FROM farms ORDER BY id;
```

Để sửa dữ liệu thử nghiệm, luôn dùng `BEGIN`, kiểm tra `SELECT`, rồi mới `COMMIT`.
Không sửa `password_hash`, `token_version`, version model hoặc schema trực tiếp.
