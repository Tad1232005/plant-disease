# Hướng dẫn Backend Tuần 4

Tuần 4 bổ sung chuỗi phân quyền: Admin cấp tài khoản chuyên môn, Manager cấp
Managed User, Manager phân công các User này vào Farm sở hữu và mọi tài khoản
chỉ thao tác trên Scan của chính mình.

## 1. Migration

```powershell
cd backend
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current
```

Head hiện tại: `f6a7b8c9d0e1` (append-only migration cho multi-model; migration
Tuần 4 gốc vẫn là `d4e5f6a7b8c9`).

`users.created_by` đã tồn tại trong initial migration (`261151a763e2`). Migration
Tuần 4 tạo `farm_members`, gồm hai FK cascade và unique constraint
`(farm_id, user_id)`. Migration mới bổ sung `added_by` để audit Manager đã gán
thành viên; dữ liệu legacy được phép NULL nên nâng cấp không làm mất dữ liệu.

Kiểm tra nhanh bằng Python/SQLite:

```powershell
.\.venv\Scripts\python.exe -c "import sqlite3; db=sqlite3.connect('plant_disease.db'); print(db.execute('pragma table_info(users)').fetchall()); print(db.execute('select sql from sqlite_master where name=?', ('farm_members',)).fetchone()[0]); db.close()"
```

## 2. Admin Users

`POST /api/v1/admin/users` chỉ nhận role `technician` hoặc `manager`:

```json
{
  "username": "manager_north",
  "email": "manager_north@example.com",
  "password": "StrongPass123!",
  "full_name": "Quản lý miền Bắc",
  "role": "manager"
}
```

Gửi role `user` hoặc `admin` nhận HTTP 422. User được tạo có `created_by` bằng
ID Admin gọi API.

`GET /api/v1/admin/users?role=manager` trả danh sách đã lọc. Chỉ Admin được gọi
hai endpoint này.

## 3. Manager Users

Request của `POST /api/v1/manager/users` cố ý không có field `role`:

```json
{
  "username": "farmer_01",
  "email": "farmer_01@example.com",
  "password": "StrongPass123!",
  "full_name": "Nông dân 01"
}
```

Service luôn ghi `role="user"` và `created_by=<manager_id>`. Nếu client cố gửi
thêm `"role":"admin"`, schema từ chối HTTP 422 thay vì âm thầm bỏ field.

`GET /api/v1/manager/users` chỉ trả role User do chính Manager hiện tại tạo.

## 4. Farm Members

Điều kiện thêm thành viên:

1. Người gọi có role Manager.
2. Farm thuộc chính Manager đó.
3. User có role `user`.
4. `user.created_by` bằng ID Manager gọi API.
5. Cặp `(farm_id, user_id)` chưa tồn tại.
6. Membership mới lưu `added_by=<manager_id>`.

```http
POST   /api/v1/farms/{farm_id}/members
GET    /api/v1/farms/{farm_id}/members
DELETE /api/v1/farms/{farm_id}/members/{user_id}
```

Body POST:

```json
{"user_id": 12}
```

Gán trùng nhận HTTP 409. DELETE chỉ xóa membership, không xóa tài khoản User.

## 5. Scans

```http
GET    /api/v1/scans/history
GET    /api/v1/scans/{scan_id}
DELETE /api/v1/scans/{scan_id}
```

Mọi role đã đăng nhập chỉ thấy hoặc thao tác Scan có `user_id` bằng chính ID
trong access token. Admin không có nhánh xem toàn bộ ở ba API này; chức năng
giám sát toàn hệ thống sẽ dùng `/admin/scans` riêng theo roadmap.

`GET /scans/history` hỗ trợ `limit` (1-100, mặc định 50) và `offset`. GET chi
tiết trả Disease Info chỉ khi Scan đủ độ tin cậy, đồng thời sắp Top-3 theo
`rank` và trả audit từng model theo execution order. DELETE commit xóa
Scan/Top-K/per-model results trước, sau đó dọn file upload trong vùng
storage an toàn; lỗi dọn file được log để không làm sai trạng thái DB.

Deliverable tự động hiện chạy xuyên suốt qua API thật: Admin tạo Manager →
Manager tạo hai Managed User → tạo Farm → gán hai member → cả hai đăng nhập và
gọi Predict với Farm → database có đúng hai Scan gắn Farm.

## 6. Test

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_managed_users.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_farm_members.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_scans.py -q
.\.venv\Scripts\python.exe -m pytest -q
```

Regression quan trọng nhất là
`test_manager_cannot_create_admin`: Manager gửi thêm role Admin phải bị từ chối
và không có record privilege-escalation nào được tạo.
