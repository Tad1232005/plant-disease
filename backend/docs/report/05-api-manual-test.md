# 5. Test API thủ công theo từng nhóm

Mở `http://127.0.0.1:8000/docs`. Swagger là cách dễ nhất: gọi `login`, copy
`access_token`, bấm **Authorize** và nhập `Bearer <token>`. Các endpoint yêu cầu
role phải dùng đúng token; không dùng tài khoản demo ở production.

## 0. Chuẩn bị

```powershell
cd C:\Project\plant-disease\backend
docker compose -f compose.postgres.yml up -d database
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m scripts.seed_week2
uvicorn app.main:app --reload
```

Kiểm tra `GET /health/live` trả `200`, rồi `GET /health/ready` trả `200` sau khi
migration đã ở revision hiện tại.

Tài khoản seed: `admin_user`, `manager_user`, `technician_user`, `normal_user`;
mật khẩu mặc định `Demo123321!`.

## 1. Auth

| API | Cách test | Kỳ vọng |
| --- | --- | --- |
| `POST /auth/register` | username/email/password mới | `201`, role `user` |
| `POST /auth/login` | tài khoản seed | `200`, access token và refresh cookie |
| `GET /auth/me` | Bearer token | đúng user/role/status |
| `POST /auth/refresh` | gửi refresh cookie | access token mới |
| `POST /auth/change-password` | Bearer + current/new password | `204`, token cũ hết hiệu lực |
| `POST /auth/logout` | Bearer hoặc cookie | `204`, refresh/access cũ không dùng lại được |

Test lỗi: password yếu hoặc field thừa phải `422`; login sai nhiều lần phải trả
`429` kèm `Retry-After` theo rate limit.

## 2. Farm, Managed User và thành viên Farm

Đăng nhập `manager_user`:

1. `POST /farms` với `{"name":"Farm test","location_text":"Đà Lạt"}` → `201`.
2. `GET /farms`, `GET /farms/{id}`, `PUT /farms/{id}` → chỉ owner truy cập được.
3. `POST /manager/users` tạo User được quản lý.
4. `POST /farms/{id}/members` với `{"user_id": <managed_user_id>}`.
5. Dùng token User đó gọi `GET /me/farms` → thấy Farm được gán.
6. `DELETE /farms/{id}/members/{user_id}` → User không còn thấy Farm.
7. `DELETE /farms/{id}` → soft archive; Farm không xuất hiện ở list thường.

Manager khác hoặc User thường phải nhận `403` khi sửa Farm không thuộc quyền.

## 3. Disease Info và proposal

- `GET /disease-info` phải có 38 nhãn sau seed.
- Admin dùng `POST`, `PUT`, `DELETE /disease-info/{label_key}` để quản lý nội dung.
- Technician dùng `POST /disease-proposals` với `label_key`,
  `base_content_version`, nội dung và severity.
- Technician xem `GET /disease-proposals/mine`.
- Admin xem `GET /admin/disease-proposals`, sau đó `PUT .../{id}/approve` hoặc
  `.../{id}/reject`.

Khi approve, gọi lại `GET /disease-info/{label_key}` và xác nhận
`content_version` tăng. Gửi base version cũ phải trả `409`.

## 4. Predict, lịch sử Scan, ảnh và Grad-CAM

1. Chọn ảnh JPG/PNG lá thật, gọi `POST /predict` dạng `multipart/form-data`:
   `file=<ảnh>`, `mode=auto`, `strategy=ensemble`.
2. Guest chạy Basic; User/Manager chạy tối đa Standard; Technician/Admin chạy
   Advanced. Chọn mode vượt quyền phải `403`.
3. Kiểm response: `models_requested == models_succeeded`, `top_k`,
   `validation_status`, `scan_id` và `decision_details`.
4. Với request đã đăng nhập: `GET /scans/history`, sau đó `GET /scans/{scan_id}`.
5. Nếu `validation_status=accepted`, gọi `POST /scans/{scan_id}/gradcam`, rồi
   `GET /scans/{scan_id}/gradcam` phải tải PNG.
6. `GET /scans/{scan_id}/image` phải trả ảnh nguồn. Tài khoản khác phải `403`.
7. `DELETE /scans/{scan_id}` → `204`; chi tiết/ảnh/Grad-CAM sau đó `404`.

Không diễn giải `is_valid_leaf` hay Grad-CAM là bằng chứng ảnh là lá. Với Scan bị
từ chối, label/treatment phải rỗng và Grad-CAM trả `409`.

## 5. Admin monitoring và vận hành

Đăng nhập Admin:

| API | Kiểm tra |
| --- | --- |
| `PATCH /admin/users/{id}/status` | suspend/active, token cũ của user bị thu hồi |
| `GET /stats/admin/overview` | tổng scan/user/farm hợp lý |
| `GET /stats/admin/recent-invalid` | chỉ Scan bị policy từ chối |
| `GET /admin/scans` | filter/pagination `limit`, `offset`, `from`, `to` |
| `GET /admin/scans/{id}/image` | trả ảnh và tạo audit event |
| `GET /stats/farm/{farm_id}` | chỉ Manager sở hữu Farm gọi được |

## 6. Test tự động trước bàn giao

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m mypy app scripts
.\.venv\Scripts\python.exe -m compileall -q app scripts tests
```

Pytest tạo/xóa DB riêng có hậu tố `_test`. Không chạy khi `TEST_DATABASE_URL`
trỏ vào database thật. Test ảnh thật có trong [04-test-and-handoff.md](04-test-and-handoff.md).
