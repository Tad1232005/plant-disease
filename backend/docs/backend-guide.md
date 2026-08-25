# Hướng dẫn chạy Backend 

## 1. Kiến trúc

```text
HTTP request
    -> app/api/v1/endpoints/* Router: parse request, dependency, status code
    -> app/services/*        Business rule: RBAC, ownership, token revoke
    -> app/crud/*            Truy vấn SQLAlchemy
    -> app/models/*          Schema, FK, CHECK, index
    -> SQLite
```

### Auth flow

```text
register -> Argon2 hash -> users
login -> access token 15 phút trong JSON
      -> refresh token 7 ngày trong HttpOnly cookie
refresh -> kiểm tra type + user id + token_version -> rotate hai token
logout -> token_version += 1 -> xóa cookie
```

`token_version` giải quyết điểm yếu của JWT thuần: xóa cookie ở trình duyệt
không làm token đã bị sao chép mất hiệu lực. Sau logout, refresh token cũ còn
đúng chữ ký và chưa hết hạn vẫn bị từ chối vì version trong DB đã tăng.

### RBAC và ownership

| Nhóm API | Public | User | Technician | Manager | Admin |
|---|:---:|:---:|:---:|:---:|:---:|
| Register/Login/Refresh | Có | Có | Có | Có | Có |
| `GET /auth/me`, Logout | Không | Có | Có | Có | Có |
| Đọc Disease Info | Có | Có | Có | Có | Có |
| Ghi Disease Info | Không | Không | Không | Không | Có |
| Quản lý Farm | Không | Không | Không | Farm sở hữu | Toàn bộ Farm |

Technician không được gọi `PUT /disease-info/{label_key}`. Vai trò này chỉ gửi
proposal ở module Approval Workflow của tuần sau. Đây là regression rule đã có
test riêng.

## 2. Sáu bảng nền tảng

| Bảng | Mục đích | Ràng buộc đáng chú ý |
|---|---|---|
| `users` | Tài khoản/RBAC | role CHECK, `token_version`, `created_by`, hai index roadmap |
| `farms` | Farm của Manager | FK owner -> users, xóa owner thì xóa Farm |
| `disease_info` | Nội dung bệnh public | `label_key` unique, severity low/medium/high |
| `scans` | Lịch sử dự đoán | User bắt buộc; Guest không tạo record |
| `scan_topk` | Top-3 của một scan | rank 1..3, một rank không lặp trong cùng scan |
| `model_versions` | Phiên bản model | partial unique index: chỉ một record active |

`scans` và `scan_topk` mới có schema ở Tuần 2; endpoint lịch sử/predict thuộc
các tuần tiếp theo.

## 3. Cài đặt và khởi động

Chạy trong `backend`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
alembic upgrade head
python -m scripts.seed_week2
uvicorn app.main:app --reload
```

Mở `http://127.0.0.1:8000/docs`. Seed tạo bốn tài khoản local, cùng mật khẩu
`123321`:

| Username | Role |
|---|---|
| `admin_user` | admin |
| `manager_user` | manager |
| `technician_user` | technician |
| `normal_user` | user |

Không dùng mật khẩu seed ở production. Muốn đổi trước khi seed:

```powershell
$env:SEED_DEMO_PASSWORD = "MatKhauDemoKhac!"
python -m scripts.seed_week2
```

## 4. Test API Auth từng bước

### 4.1 Register

`POST /api/v1/auth/register`

```json
{
  "username": "farmer01",
  "email": "farmer01@example.com",
  "password": "StrongPass123!",
  "full_name": "Nguyễn Văn A"
}
```

Mong đợi: HTTP 201, role `user`, không có `password` hoặc `password_hash` trong
response. Gửi lại username/email cũ phải nhận HTTP 400.

### 4.2 Login

`POST /api/v1/auth/login`

```json
{
  "username": "farmer01",
  "password": "StrongPass123!"
}
```

Mong đợi: HTTP 200 và `access_token`. Header `Set-Cookie` phải có `HttpOnly`,
`Path=/api/v1/auth`, thời hạn 7 ngày. Sai mật khẩu nhận HTTP 401.

Trong Swagger, bấm **Authorize** và dán access token. Swagger tự thêm tiền tố
Bearer theo OAuth2 scheme, không cần tự ghi `Bearer` trong ô token.

### 4.3 Me

`GET /api/v1/auth/me`

- Không Authorize: HTTP 401.
- Có access token: HTTP 200 và đúng user hiện tại.
- Đưa refresh token vào Authorization header: HTTP 401 vì sai token type.

### 4.4 Refresh

`POST /api/v1/auth/refresh`

Cookie được browser/Swagger gửi tự động. Mong đợi HTTP 200, access token mới và
refresh cookie mới. Không có cookie hoặc cookie sai/hết hạn nhận HTTP 401.

### 4.5 Logout và revoke

`POST /api/v1/auth/logout` cần access token. Mong đợi HTTP 204. Sau đó gọi lại
Refresh phải nhận HTTP 401. Việc này chứng minh không chỉ cookie bị xóa mà
`token_version` trong DB đã vô hiệu refresh token cũ.

## 5. Test API Farm từng bước

Đăng nhập `manager_user`, Authorize bằng access token.

1. `POST /api/v1/farms` với:

   ```json
   {
     "name": "Trang trại Đà Lạt",
     "location_text": "Lâm Đồng"
   }
   ```

   Mong đợi HTTP 201; `owner_id` là id của Manager.

2. `GET /api/v1/farms`: HTTP 200, Manager chỉ thấy Farm của mình.
3. `GET /api/v1/farms/{id}`: HTTP 200 nếu sở hữu.
4. `PUT /api/v1/farms/{id}` với một hoặc cả hai field: HTTP 200.
5. `DELETE /api/v1/farms/{id}`: HTTP 204; GET lại nhận 404.

Case phân quyền cần kiểm tra:

- `normal_user` POST Farm -> 403.
- Manager khác GET/PUT/DELETE Farm không sở hữu -> 403.
- `admin_user` GET danh sách -> thấy toàn bộ Farm của mọi Manager.
- Tên chỉ chứa khoảng trắng -> 422.

Case Manager khác được test tự động trong `tests/test_farms.py`; không cần sửa
role trực tiếp trong DB để test thủ công.

## 6. Test API Disease Info từng bước

Hai endpoint GET là public. Các endpoint POST/PUT/DELETE chỉ Admin.

1. Không đăng nhập, gọi `GET /api/v1/disease-info`: HTTP 200.
2. Không đăng nhập, gọi `GET /api/v1/disease-info/{label_key}`: HTTP 200 hoặc
   404 nếu label không tồn tại.
3. Đăng nhập `admin_user`, POST:

   ```json
   {
     "label_key": "Demo___Leaf_spot",
     "disease_name": "Bệnh đốm lá demo",
     "description": "Dữ liệu dùng để test.",
     "treatment": "Loại bỏ lá bệnh.",
     "severity_level": "medium"
   }
   ```

   Mong đợi HTTP 201. Tạo lại label giống nhau nhận HTTP 400.

4. PUT cùng label với `{"severity_level":"high"}`: HTTP 200.
5. DELETE cùng label: HTTP 204.
6. Đăng nhập `technician_user`, thử PUT: HTTP 403.
7. Gửi severity ngoài `low`, `medium`, `high`: HTTP 422.

## 7. Test tự động

Không cần chạy Uvicorn:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Chạy theo module để học từng phần:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_auth.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_farms.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_disease_info.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_schema_week2.py -q
```

Các test dùng SQLite in-memory và tạo/xóa schema riêng cho từng case, nên không
đụng vào `plant_disease.db` của bạn.

## 8. Smoke test trên server thật

Sau khi migration, seed và chạy Uvicorn, mở terminal thứ hai:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_week2.py
```

Script gọi tuần tự Register -> Login -> Me -> Refresh -> Logout, sau đó CRUD
Farm bằng Manager và CRUD Disease Info bằng Admin. Mỗi bước in `[PASS]` cùng
HTTP status; lỗi nào xảy ra script dừng ngay và in response body.

## 9. Migration và thay đổi DB hiện có

```powershell
alembic current
alembic upgrade head
alembic current
```

## 10. Lỗi thường gặp

- **401 ở `/auth/me`**: access token chưa được đặt trong Authorize hoặc đã hết
  15 phút.
- **401 ở `/auth/refresh`**: cookie không tồn tại, path/domain không khớp, hoặc
  user đã logout làm `token_version` tăng.
- **403 ở Farm**: đang dùng role User/Technician hoặc Manager không sở hữu Farm.
- **403 ở Disease Info**: chỉ Admin được ghi; Technician không phải Admin.
- **422**: JSON sai schema, tên trống, password quá ngắn hoặc severity sai.
- **SQLite báo thiếu cột**: chưa chạy `alembic upgrade head` trước khi seed/chạy
  server.
