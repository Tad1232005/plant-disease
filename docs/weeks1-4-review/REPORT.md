# Báo cáo kiểm thử và bổ sung backend Tuần 1–4

Ngày: 07/09/2026. Phạm vi: backend hiện có, không sửa frontend, không tự triển khai nghiệp vụ tuần 5–8.

## 1. Kết quả thực tế

- Baseline: 112 test đạt.
- Sau bổ sung: **144 test đạt**, 2 cảnh báo thư viện, thời gian 44,01 giây. Thêm 32 trường hợp regression trong `backend/tests/test_weeks1_4_review.py`.
- `mypy app tests scripts`: đạt, 81 source file.
- `compileall`: đạt. `git diff --check`: không phát hiện lỗi whitespace; Git chỉ cảnh báo chuyển LF/CRLF.
- Test suite chạy trên PostgreSQL 18 tách biệt, không dùng dữ liệu ứng dụng để chạy test phá hủy.
- Bộ test có chạy HTTP inference với ba file model thật, kiểm basic/standard/advanced, lưu Scan vào PostgreSQL và đọc ảnh theo quyền. Không chỉ mock toàn bộ ML.
- Test migration kiểm nâng revision cũ lên head, giữ Scan lịch sử và downgrade trên database test.
- Database ứng dụng PostgreSQL 17.11 đã kết nối được ở cuối lượt làm việc; đã nâng `f6a7b8c9d0e1` → `a7b8c9d0e1f2`. `alembic check`: không phát hiện thay đổi schema cần migration thêm.
- Chạy seed trên DB ứng dụng: `+0 user, +0 disease_info, +0 model_version`. Dữ liệu đã đủ nên không tạo trùng.
- Smoke đọc qua TestClient dùng DB ứng dụng: disease-info 200, capabilities 200, me/farms không đăng nhập 401. Đây không phải kiểm thử mạng qua Uvicorn đang chạy.

Hai cảnh báo còn lại thuộc tương thích Starlette/httpx và API phiên bản của argon2/passlib. Không nâng dependency hàng loạt trong lượt sửa nghiệp vụ này; cần xử lý trong đợt kiểm tra dependency riêng.

## 2. Tuần 1 — Auth và tài khoản

### Những gì hiện có

Register mặc định user; hash Argon2; login cấp access JWT 15 phút, refresh 7 ngày trong HttpOnly Cookie; refresh, me, logout; kiểm role bằng tài khoản trong DB; `token_version` thu hồi cả access và refresh.

### Đã bổ sung/sửa lần này

1. **Logout tăng token_version bằng biểu thức SQL nguyên tử.** Trước đây hai session cùng đọc version 0 rồi ghi 1 có thể làm mất một lần tăng. Nay mỗi UPDATE thực hiện `token_version = token_version + 1` tại DB. Test dùng hai session đã đọc cùng version cũ để tái hiện lost-update; kết quả cuối là 2.
2. **Đổi mật khẩu:** `POST /api/v1/auth/change-password`. Nhận mật khẩu hiện tại và mật khẩu mới, khóa dòng User, kiểm phiên còn hiệu lực, xác minh mật khẩu cũ, ghi hash mới và tăng version trong cùng transaction. Thành công 204 và xóa refresh cookie. Người dùng phải đăng nhập lại; mọi token cũ nhận 401. Mật khẩu sai/trùng cũ nhận 400; không đạt chính sách nhận 422; trường hợp thất bại không thu hồi phiên hợp lệ.
3. **JWT bắt buộc exp/iat/sub.** Token thiếu trường bắt buộc bị từ chối, không vô tình chấp nhận token không có hạn sử dụng.
4. **Optional auth không hạ token lỗi thành Guest.** Không gửi Authorization thì được dùng public; đã gửi header sai scheme/rỗng thì 401, kể cả capabilities.
5. **Một chính sách mật khẩu chung** cho register, cấp tài khoản và đổi mật khẩu: 8–128 ký tự, có chữ hoa/chữ thường/chữ số. Email giới hạn 100 ký tự khớp schema DB, trả 422 trước khi INSERT nếu quá dài.
6. **CLI đổi role khóa dòng User** trước khi cập nhật để không làm mất lần tăng token_version khi trùng logout/đổi mật khẩu.

Tệp chính: `app/services/auth_service.py`, `app/core/security.py`, `app/api/deps.py`, `app/schemas/auth.py`, `app/schemas/user.py`, `scripts/update_role.py`.

Giới hạn: token_version là thu hồi toàn tài khoản, không phải quản lý từng thiết bị. Chưa có refresh-family replay detection, reset mật khẩu qua email, hay workflow khóa tài khoản admin. Không coi các chức năng đó đã hoàn thiện.

## 3. Tuần 2 — CRUD, schema và seed

### Những gì hiện có

Farm CRUD chỉ Manager và Farm sở hữu, gồm GET chi tiết. Farm dùng soft-delete. Disease Info đọc public, ghi chỉ Admin; xóa là ẩn nội dung. Index users role/created_by, CHECK và foreign key được test. Seed đủ 38 nhãn của bundle và ba model version độc lập; chạy lặp không ghi đè nội dung Admin sửa.

### Đã bổ sung/sửa lần này

- FarmUpdate không nhận `name: null`; DiseaseInfoUpdate không nhận `disease_name: null` hoặc `severity_level: null`. Trả 422, không còn đi tới lỗi NOT NULL trong DB. Bỏ qua field vẫn giữ giá trị cũ; field tùy chọn như location/description/treatment vẫn được xóa bằng null.
- Các schema ghi Farm/Disease Info từ chối field ngoài hợp đồng. Không cho client âm thầm gửi owner_id, archived_at, updated_by, is_active… Các field quản trị do server quyết định. Client nào trước đây gửi kèm field thừa sẽ cần bỏ field đó để tránh 422.
- GET `/farms` và `/disease-info` có `limit` tùy chọn 1–100, `offset` >= 0, phân trang tại SQL. Không gửi limit vẫn giữ hành vi và dạng mảng cũ để tránh cắt dữ liệu đột ngột ở FE.
- Bắt IntegrityError khi tạo Disease Info để rollback và trả 400 nếu dữ liệu xung đột giữa kiểm tra trùng và commit.
- Service Farm tự kiểm role Manager, không chỉ phụ thuộc lớp HTTP.

Chưa áp dụng phân trang mới cho danh sách admin/users, manager/users và Farm Members; đây là phần cần bổ sung trước khi dữ liệu lớn. Thêm label trong Disease Info chỉ thêm nội dung tra cứu, không tự mở rộng lớp đầu ra của model.

### Database sau kiểm tra

Vẫn 8 bảng nghiệp vụ, không thêm bảng cho các endpoint mới:

| Bảng | Chức năng | Số dòng DB local sau thao tác |
|---|---|---:|
| users | Tài khoản, role, người tạo, hash mật khẩu, token_version | 4 |
| farms | Farm, Manager sở hữu, thông tin địa điểm, soft-delete | 0 |
| farm_members | Phân công User vào Farm; unique farm_id/user_id | 0 |
| disease_info | Nội dung tra cứu theo label_key, mức độ, xử lý | 38 |
| model_versions | Artifact/version, temperature, checksum, bật/active | 3 |
| scans | Kết quả tổng hợp, owner/Farm, trạng thái và snapshot inference | 0 |
| scan_topk | Top-3 tổng hợp cho mỗi Scan | 0 |
| scan_model_results | Kết quả và audit của từng model trong Scan | 0 |

Model version vẫn chỉ cho một active version **mỗi model_type**, không phải một active cho toàn hệ thống. Ba model_type hỗ trợ hiện tại là EfficientNet-B0, MobileNetV2, ResNet50.

Migration áp dụng lần này đã được viết trong đợt tuần 3 trước: chỉ thêm `scans.inference_snapshot JSONB NULL`. Không DROP bảng/dữ liệu. Không cần PRAGMA SQLite vì backend hiện dùng PostgreSQL. Không thay `.env` hay mật khẩu PostgreSQL.

## 4. Tuần 3 — Predict và ba model

### Kiểm lại phần đã làm trước

- Preprocessing RGB, resize trực tiếp 224×224, bilinear/antialias, ToTensor và ImageNet normalization; không center crop.
- Guest Basic; User/Manager tối đa Standard; Technician/Admin tối đa Advanced. Server chặn mode vượt quyền.
- Kiểm artifact, thứ tự 38 class, checksum, temperature; logits sai shape/NaN/Inf bị từ chối.
- Giới hạn upload, decode ảnh, timeout, giới hạn concurrency/cache; trả lỗi thay vì lưu kết quả hỏng.
- Guest không lưu Scan; tài khoản lưu ảnh, Scan, top-k, kết quả từng model và snapshot cấu hình thực chạy.
- Rollback và dọn ảnh khi DB lỗi; kiểm lại phiên sau inference trước khi lưu.
- HTTP test dùng model thật đã đạt cả ba mode; đây là kiểm tra tích hợp, không phải xác minh lại accuracy/F1 của tập test ML.

### Bổ sung lần này

Điều kiện gắn Scan vào Farm của Managed User yêu cầu owner hiện vẫn là Manager, ngoài kiểm membership và created_by. Tránh giữ quyền phân công dựa trên role đã cũ sau khi đổi role.

**Không thay threshold 0.3.** Temperature scaling không biến classifier thành bộ phát hiện lá/OOD. Báo cáo probe tuần 3 trước có 14/24 lượt ảnh tổng hợp được chấp nhận, nên vẫn có false acceptance. UI cần diễn đạt là “đủ/không đủ độ tin cậy theo policy”, không khẳng định đã xác minh ảnh là lá. Cần tập ảnh thực tế trong/ngoài miền và tiêu chí false accept/reject để nghiệm thu chất lượng.

## 5. Tuần 4 — Managed User, thành viên và Scan

### Đã bổ sung/sửa lần này

- Shared service cấp tài khoản tự chặn cặp creator/role/request không hợp lệ: Admin + AdminCreateUserRequest chỉ technician/manager; Manager + ManagerCreateUserRequest chỉ user. Gọi trực tiếp service cũng không vượt được quy tắc này.
- FarmMember user_id phải là số nguyên dương thực sự, không nhận boolean/chuỗi/số âm. Service quản lý thành viên tự kiểm role Manager.
- **GET `/api/v1/me/farms`** giúp chọn Farm khi predict mà không mở CRUD cho User. Manager thấy Farm sở hữu; Managed User thấy Farm chưa archive, có membership, owner đúng created_by và vẫn là Manager. User độc lập/Technician/Admin nhận `[]`; Guest 401. Chỉ trả id/name/location_text, không lộ danh sách thành viên. Mặc định limit 50, tối đa 100, có offset.
- Dữ liệu JSON top-k audit bị hỏng được kiểm schema từng phần tử. Bỏ phần tử thiếu trường, confidence ngoài [0,1]/NaN hoặc rank ngoài 1–3 và ghi log, tránh lỗi 500 ở Scan detail. Không sửa hay bịa lại dữ liệu lịch sử trong DB.
- Giữ nguyên Scan owner-only: Admin không được xem/xóa ảnh hoặc Scan của người khác qua API cá nhân.

Deliverable đã test: Admin tạo Manager → Manager tạo hai User → tạo Farm → gán hai thành viên → đọc đúng hai thành viên → User thấy Farm được giao nhưng không được GET danh sách CRUD Farms → gỡ membership thì Farm biến mất khỏi lựa chọn, tài khoản vẫn tồn tại → archive Farm thì Manager không còn thấy Farm trong lựa chọn.

## 6. API hiện có — không nhầm với roadmap tương lai

Tất cả đường dẫn dưới có prefix `/api/v1`. OpenAPI hiện có 30 operation nghiệp vụ, thêm GET `/` ở root phục vụ trạng thái cơ bản.

| Nhóm | Method và endpoint | Quyền |
|---|---|---|
| Auth | POST /auth/register, /auth/login | Public |
| Auth | POST /auth/refresh | Refresh cookie |
| Auth | GET /auth/me; POST /auth/logout, /auth/change-password | Đăng nhập |
| Predict | GET /predict/capabilities; POST /predict | Public hoặc đăng nhập; mode theo role |
| Farm | POST/GET /farms; GET/PUT/DELETE /farms/{farm_id} | Manager; giới hạn sở hữu |
| Thành viên | POST/GET /farms/{farm_id}/members; DELETE /farms/{farm_id}/members/{user_id} | Manager sở hữu |
| Nội dung | GET /disease-info; GET /disease-info/{label_key} | Public |
| Nội dung | POST /disease-info; PUT/DELETE /disease-info/{label_key} | Admin |
| Cấp tài khoản | POST/GET /admin/users | Admin |
| Managed User | POST/GET /manager/users | Manager |
| Scan cá nhân | GET /scans/history; GET/DELETE /scans/{scan_id}; GET /scans/{scan_id}/image | Chủ sở hữu |
| Chọn Farm | GET /me/farms | Đăng nhập, lọc theo quan hệ thực tế |

Chưa có API admin đổi cấu hình Basic/Standard/Advanced, CRUD Model Versions, admin/scans, disease proposals/approval, stats hay Grad-CAM. Model metadata và seed hiện có không đồng nghĩa các API quản trị đó đã làm xong.

## 7. Hướng dẫn tự test

### Chạy bộ tự động

Trong `C:\Project\plant-disease\backend`, PostgreSQL cấu hình trong `.env` phải đang chạy:

```powershell
.\.venv\Scripts\python.exe -m scripts.check_database
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic check
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m mypy app tests scripts
```

Pytest mặc định tạo/xóa `plant_disease_test`, và migration test dùng `plant_disease_migration_test` trên server được chọn. Tài khoản test cần quyền tạo database. Nếu dùng TEST_DATABASE_URL thì chọn database chuyên test với hậu tố `_test`. Không đặt tên DB dữ liệu thật vào biến này, không chạy hai suite đồng thời trên cùng server/tên test. Fixture sẽ DROP/CREATE database test, không chỉ rollback từng case. Không cần dùng cổng tạm 55439 của phiên kiểm thử này.

### Test tay bằng Swagger

Khởi động `python -m uvicorn app.main:app --reload`, mở `http://127.0.0.1:8000/docs`. Các thao tác sau sẽ tạo/sửa dữ liệu local nên dùng tài khoản thử riêng.

1. Register User mới, login, copy `access_token` vào Authorize. Không dùng refresh token làm Bearer.
2. GET auth/me = 200. POST auth/change-password với `current_password` và `new_password` hợp lệ = 204. Dùng access cũ gọi me = 401; login mật khẩu cũ = 401; login mật khẩu mới = 200. Đổi mật khẩu seed nếu test bằng seed thì mật khẩu thật của tài khoản đó cũng thay đổi.
3. Login Admin, POST admin/users role manager; thử role admin phải 422. Login Manager mới, POST manager/users không gửi role để tạo hai User; gửi role admin phải 422.
4. Manager POST farms, GET farms/{id}; dùng Manager khác hoặc Admin thử truy cập phải bị từ chối. PUT name null = 422; PUT location_text null = 200.
5. Gán hai User vừa tạo vào members = 201; gán trùng = 409; gán User do Manager khác tạo = 403; GET members có đúng danh sách.
6. Login User được gán: GET me/farms có Farm tương ứng; GET farms vẫn 403. Gỡ membership rồi GET me/farms phải không còn Farm đó.
7. Admin tạo/sửa/ẩn disease-info; Public đọc được nội dung đang active, không ghi được. PUT severity_level null = 422. Thử GET disease-info?limit=1&offset=1.
8. POST predict multipart với ảnh JPEG/PNG; Guest/đăng nhập lần lượt kiểm các mode cho phép. User yêu cầu advanced phải 403. Guest không có scan_id; User có Scan lưu được khi request thành công. Đọc history/detail/image bằng owner; Admin khác owner vẫn bị từ chối. Ảnh tổng hợp có thể vẫn được model chấp nhận: đó là hạn chế OOD, không phải lỗi phân quyền.
9. Logout rồi thử lại Bearer cũ phải 401. Refresh cookie cũ cũng không dùng lại được sau logout/đổi mật khẩu.

## 8. Ảnh hưởng và phần còn cần làm

Không sửa frontend. Hai endpoint mới là bổ sung; FE chỉ cần tích hợp khi muốn dùng đổi mật khẩu và chọn Farm. Payload ghi gửi field thừa/null bắt buộc nay nhận 422 có chủ đích. Sau đổi mật khẩu FE cần xóa access token đang giữ và quay về login.

Tuần 1–4 đã qua bộ kiểm thử hiện có và các regression bổ sung, đủ tiếp tục phát triển trên local. Chưa phải kết luận production-ready: còn đánh giá OOD trên dữ liệu thật, rate limit/chống brute-force và spam Guest, HTTPS/cookie theo môi trường, CSRF nếu triển khai cookie cross-site, backup/restore, benchmark RAM/concurrency nhiều worker, phân trang danh sách còn lại và quản trị model/workflow tuần sau. Không thêm tính năng thanh toán hay quyền Admin chỉnh tier trong lượt này.
