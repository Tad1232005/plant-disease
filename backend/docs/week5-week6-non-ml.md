# Backend tuần 1–6: phần không phụ thuộc ML

Ngày thực hiện: 15/09/2026. Phạm vi: chỉ backend; không sửa frontend, ml,
trọng số, temperature, model registry, ngưỡng hoặc thuật toán inference.
Tài liệu này cập nhật hiện trạng kỹ thuật; ba Word ngày 07/09 vẫn là bản thiết kế cũ.

## 1. Những phần tuần cũ đã khép kín

- Đã kiểm thử tích hợp lại đổi mật khẩu, thu hồi token, Farm/Disease CRUD,
  `/me/farms`, ảnh Scan riêng tư và các ca null/field ngoài schema.
- Bổ sung phân trang cho Admin Users, Manager Users và Farm Members. Cùng
  quy ước các danh sách: `limit=50`, tối đa 100, `offset>=0`, sắp xếp ổn định.
  Response vẫn là array; FE phải lấy trang tiếp theo khi cần toàn bộ dữ liệu.
- Logout tăng token_version bằng SQL nguyên tử, tránh mất lần tăng khi đồng thời.
- Service cấp tài khoản tự kiểm role; không chỉ tin route đã hardcode role.
- Không gán thêm Farm Member khi User đang bị khóa. Membership cũ và lịch sử
  vẫn được giữ, không xóa dây chuyền tài khoản hoặc dữ liệu.
- Trước khi lưu Scan, kiểm lại status/token_version và khóa row User đến commit.
  Farm/membership cũng được kiểm lại, owner phải trùng created_by của Managed User.
  Nếu bị thu hồi phiên trong lúc request chạy: 401, không lưu Scan/ảnh mới.
  Đây là bảo vệ persistence, không thay đổi đầu ra model.

## 2. Endpoint tuần 5

Tất cả đường dẫn có tiền tố `/api/v1`.

| Method | Đường dẫn | Quyền | Chức năng |
| --- | --- | --- | --- |
| PATCH | /admin/users/{user_id}/status | Admin | Khóa/mở tài khoản với lý do |
| GET | /stats/farm/{farm_id} | Manager sở hữu | Tổng hợp Scan gắn Farm chưa archive |
| GET | /stats/admin/overview | Admin | Tổng Scan, User và Farm toàn hệ thống |
| GET | /stats/admin/recent-invalid | Admin | Scan bị policy từ chối; không phải danh sách ảnh đã xác nhận không lá |
| GET | /admin/scans | Admin | Danh sách giám sát riêng, có filter và phân trang |
| GET | /admin/scans/{scan_id}/image | Admin | Ảnh giám sát riêng, bắt buộc ghi audit trước khi trả file |

### Khóa/mở tài khoản

```json
{"status":"suspended","reason":"Tạm khóa để kiểm tra tài khoản"}
```

`status`: active hoặc suspended. reason phải có nội dung, tối đa 1000 ký tự.
Trả UserResponse có field status. Không generic sửa role, password hoặc created_by.
Không cho Admin tự khóa mình; không cho mất Admin active cuối. Các chuyển trạng
thái dùng transaction lock chung và đọc lại quyền actor sau khi lấy lock, tránh
hai Admin khóa chéo khiến không còn người quản trị.

Mỗi lần đổi trạng thái thực sự tăng token_version và ghi audit cùng transaction.
Gửi lại đúng trạng thái hiện hành là no-op, không tăng version/audit lần nữa.
Login, refresh và dependency access đều từ chối tài khoản suspended bằng 401.
Mở khóa không khôi phục token cũ: phải login lại. Manager không được khóa User.

### Bộ lọc và cách tính thống kê

- `from`, `to`: ISO 8601 bắt buộc có timezone; ví dụ `2026-09-15T00:00:00Z`.
  Khoảng `[from, to)`: gồm đầu, không gồm cuối. Đảo khoảng/thiếu timezone trả 422.
- `/admin/scans`: thêm `user_id`, `validation_status`, `is_valid_leaf`.
- Scan lists: limit/offset; mới nhất trước, id phá hòa khi timestamp bằng nhau.
- `total_scans = accepted_scans + rejected_scans + legacy_scans`.
- Accepted: không phải inference_mode legacy, validation_status accepted và cờ
  tương thích is_valid_leaf=true. Đây vẫn không phải xác nhận ảnh là lá.
- Legacy tách riêng, không tự suy diễn lại kết quả cũ.
- `rejection_rate = rejected / (accepted + rejected)`, 0..1; null khi chưa có
  Scan có thể phân loại. Legacy không làm loãng tỷ lệ này.
- `disease_counts` chỉ tính nhãn từ Scan accepted; một Scan tính một lần, không
  join scan_model_results để cộng trùng. Tổng theo Farm dựa trên farm_id đã lưu,
  không dựa vào membership hiện tại của người tạo Scan.
- Overview áp dụng from/to cho Scan. Tổng User/Farm là inventory hiện tại,
  gồm cả suspended/archived; active_users/active_farms báo riêng phần hoạt động.
- Thống kê phản ánh dữ liệu đang tồn tại; Scan bị chủ sở hữu xóa không còn được đếm.

Các kết nối ứng dụng mới dùng timezone UTC. Timestamp Scan cũ vẫn là kiểu không
timezone: dữ liệu lịch sử đang được đọc theo quy ước UTC; chưa dịch giờ dữ liệu
cũ vì chưa xác minh timezone lúc nó được ghi. Không tự chuyển hàng loạt timestamp.

### Phân quyền ảnh

Admin vẫn bị 403 tại `/scans/{id}/image` của người khác, phải dùng namespace
`/admin/scans/{id}/image`. Các API Farm dành Manager không mở cho Admin.
Ảnh chỉ lấy từ UPLOAD_DIR, JPEG/PNG, Cache-Control private/no-store và nosniff.
Audit `scan.image_access_authorized` ghi việc cấp phép phục vụ ảnh, không khẳng
định client đã tải đủ file. Nếu không ghi được audit thì không trả ảnh.

## 3. Endpoint tuần 6: đề xuất nội dung

| Method | Đường dẫn | Quyền | Chức năng |
| --- | --- | --- | --- |
| POST | /disease-proposals | Technician | Gửi bản nội dung thay thế cho nhãn có sẵn |
| GET | /disease-proposals/mine | Technician | Chỉ đề xuất mình gửi; filter status |
| GET | /admin/disease-proposals | Admin | Queue; filter status, label_key, proposer_id, from/to |
| PUT | /admin/disease-proposals/{id}/approve | Admin | Duyệt nội dung đúng revision |
| PUT | /admin/disease-proposals/{id}/reject | Admin | Từ chối với review_note |

Các list đều có limit/offset. Admin không gửi proposal thay Technician. Không
cấp generic update/delete proposal, không nhận reviewer_id/status từ client.

### Quy trình thử trên Swagger

1. Đăng nhập Technician, Authorize access token; GET disease-info của nhãn cần sửa.
2. Lấy content_version mới nhất; POST /disease-proposals với:

```json
{
  "label_key": "Tomato___Early_blight",
  "base_content_version": 1,
  "disease_name": "Tên bệnh đã rà soát",
  "description": "Mô tả đề xuất",
  "treatment": "Hướng dẫn đề xuất",
  "severity_level": "medium"
}
```

Giá trị 1 chỉ là ví dụ; phải dùng version vừa đọc. Đây là bản thay thế nội dung:
description/treatment không gửi sẽ nhận null, severity không gửi mặc định medium.
Không phải PATCH từng field. Nhãn phải đang tồn tại và active; không sinh nhãn ML.

3. Trả 201 pending; Technician xem GET /disease-proposals/mine.
4. Đăng nhập Admin; GET /admin/disease-proposals?status=pending.
5. PUT approve không cần body, hoặc PUT reject với
   `{"review_note":"Cần bổ sung nguồn kiểm chứng nội dung"}`.
6. Sau approve: GET disease-info trả nội dung mới, content_version tăng 1.

Approve khóa proposal và content, kiểm active + base_content_version, áp dụng
cùng hàm CRUD không commit trung gian, ghi người duyệt/trạng thái/audit rồi
commit một lần. Thiếu record: 404; revision lỗi hoặc quyết định đối nghịch: 409.
Reject không sửa nội dung; note trống/thiếu: 422. Gửi lại cùng quyết định trả
record đã duyệt, giữ reviewer/note/thời gian và không ghi lặp audit.

Direct update/archive/restore Disease Info đều tăng content_version, do đó đề
xuất cũ không thể ghi đè thay đổi mới hoặc tự khôi phục nội dung đã bị ẩn.
Audit failure phải rollback transaction, không được xuất bản dở dang.

## 4. Database và migration

Head mới: `c9d0e1f2a3b4`, sau `b8c9d0e1f2a3`. Có 10 bảng nghiệp vụ:
8 bảng cũ + disease_proposals + audit_events; không tính alembic_version.

- users.status VARCHAR20 NN default active, CHECK active/suspended.
- users.token_version có CHECK >=0.
- disease_info.content_version INTEGER NN default 1, CHECK >=1.
- disease_proposals: tác giả, nhãn, bản nội dung, base version, status
  pending/approved/rejected, reviewer, note, thời gian có timezone; CHECK bảo vệ
  type update_content, version, severity, trạng thái và reason khi rejected.
- audit_events: actor FK SET NULL, action, resource_type/id, outcome, metadata
  JSONB đã chọn field, created_at có timezone. Ứng dụng chỉ append, không có API
  sửa/xóa. Không tự động ghi password, token, hash hoặc bytes ảnh vào audit.

Migration giữ dữ liệu cũ, bổ sung default; không sửa hoặc stamp migration cũ.
Đã thử nâng từ f6 có User/Disease/Scan cũ, kiểm dữ liệu + default, chạy Alembic
check và downgrade base CHỈ trên database test. Không chạy downgrade DB thật:
thao tác đó sẽ mất audit/proposal/status/version mới.

**Chưa migrate database ứng dụng**. Trước khi chạy backend mới:

```powershell
# Trong backend, sau khi backup và xác nhận .env trỏ đúng DB muốn nâng cấp.
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic check
```

Sau đó restart API. Code mới cần schema mới; không chỉ restart khi chưa migrate.

## 5. Kiểm thử

Dùng PostgreSQL 18 tạm, localhost:55439, cluster riêng trong TEMP. Không đổi .env,
không ghi vào database ứng dụng. Lượt kiểm tra thực tế và số test cuối được ghi
ở phần kết quả bên dưới. Dữ liệu ảnh trong test là file tạm/fixture; inference
được mock khi test quyền hoặc persistence, không đánh giá accuracy.
Sau khi kiểm thử xong đã dừng server và xóa duy nhất cluster tạm do lượt này tạo;
không xóa dữ liệu ứng dụng. Cổng test 55439 không được giữ chạy sau bàn giao.

Chạy lại khi server PostgreSQL dành cho test đã sẵn sàng và tài khoản có CREATEDB:

```powershell
# TEST_DATABASE_URL có thể chỉ định riêng; database bắt buộc hậu tố _test.
# Nếu không đặt, fixture lấy credentials trong .env và dùng tên DB test riêng.
.\.venv\Scripts\python.exe -m pytest -q --ignore=tests/test_predict_downloaded_samples.py -k "not real_artifact_contract"
.\.venv\Scripts\python.exe -m mypy app tests scripts
```

Fixture tạo/xóa DB có hậu tố _test; không dùng tên chứa dữ liệu thật, không chạy
hai suite đồng thời trên cùng tên DB. Model metadata/response giả được dùng cho
test tích hợp; kiểm artifact bàn giao và audit ảnh với trọng số thật được bỏ qua.

### Kết quả

Kết quả cuối: **148 passed, 1 deselected**, 127,99 giây; file test ảnh thật được
ignore. Mypy đạt **92 source files**; compileall đạt; session timezone xác nhận
UTC. Có hai cảnh báo dependency Starlette/httpx và argon2/passlib, không phải lỗi
test. Migration check/upgrade/downgrade và bảo toàn dữ liệu legacy đều nằm trong
bộ test này. 28 ca trong test_operations_workflow.py bao phủ phần mới, gồm cạnh
tranh trạng thái tài khoản, duyệt đồng thời, revision cũ, rollback, quyền ảnh,
giới hạn danh sách, thống kê và thu hồi phiên trước khi lưu Scan.

## 6. Những gì vẫn hoãn

- Model registry/activation/rollback, policy model, inference_snapshot đầy đủ,
  leaf detection/OOD/calibration/benchmark và Grad-CAM: bỏ qua theo yêu cầu.
- Staging/deploy chưa thực hiện: cần môi trường đích và cấu hình triển khai.
- Backup/restore ứng dụng và kiểm thử tải là việc vận hành các tuần sau, chưa
  được chứng nhận chỉ nhờ API tests.
- Không cập nhật frontend hoặc xuất lại ba Word trong lượt code này. FE có thể
  dựa vào OpenAPI và hợp đồng trên để tích hợp các field/endpoint mới.

Không kết luận toàn bộ 6 tuần đã hoàn thành: chỉ các luồng backend không phụ
thuộc ML nêu trong tài liệu đã được triển khai.
