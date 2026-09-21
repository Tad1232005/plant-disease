# Bổ sung backend không phụ thuộc ML — 15/09/2026

> Cập nhật ở lượt tiếp tục: các test tích hợp đã chạy trên PostgreSQL tạm; status,
> audit, phân trang còn lại và workflow tuần 5–6 đã được bổ sung. Các mục chưa
> kiểm chứng/chưa làm bên dưới là ghi nhận của lượt đầu, không phải hiện trạng
> mới nhất. Xem [báo cáo tiếp tục](week5-week6-non-ml.md).

## Phạm vi đã làm

Chỉ backend. Không sửa frontend, ml, trọng số, temperature, threshold hoặc dữ liệu
ứng dụng. Không có migration mới trong lượt này; giữ nguyên các thay đổi chưa
commit của những lượt trước.

### Tuần 1: đổi mật khẩu

`POST /api/v1/auth/change-password`, Bearer token, JSON:

```json
{"current_password":"StrongPass123!","new_password":"NewStrongPass456!"}
```

Trả 204, xóa refresh cookie, cập nhật hash Argon2 và tăng token_version trong cùng
transaction. Access/refresh token cũ không còn dùng được; phải đăng nhập lại.
400 nếu mật khẩu hiện tại sai hoặc mật khẩu mới giống cũ; 422 nếu không đạt quy
tắc chữ hoa/chữ thường/chữ số, độ dài 8–128 hoặc chứa field không được phép.
Conditional UPDATE chống ghi đè khi tài khoản vừa thay đổi đồng thời (409).

### Tuần 2: CRUD và phân trang

Farm/Disease create/update từ chối field ngoài schema bằng 422. Update từ chối
null cho name/disease_name/severity_level; field bị bỏ qua giữ giá trị cũ.
location_text/description/treatment vẫn được gửi null để xóa nội dung tùy chọn.
Không cho đổi owner_id hoặc label_key qua update.

GET /farms và /disease-info bổ sung limit (mặc định 50, tối đa 100), offset >= 0.
Response vẫn là array. Client có hơn 50 bản ghi phải lấy các trang tiếp theo;
không suy ra response đầu tiên là toàn bộ danh mục. Scan history vốn đã có phân
trang, không sửa lại. Các danh sách account/membership khác chưa bổ sung trong lượt này.

### Tuần 4: Farm được giao và ảnh riêng tư

GET /api/v1/me/farms: cần đăng nhập, có limit/offset như trên.
Manager thấy farm sở hữu chưa archive. Managed User chỉ thấy farm có membership
và owner trùng created_by. User độc lập, Technician, Admin nhận []. Không cấp
Farm CRUD hay quyền xem Scan người khác. Farm archive không còn xuất hiện.

GET /api/v1/scans/{scan_id}/image: chỉ chủ Scan, Admin không có bypass.
401 nếu chưa đăng nhập; 403 nếu không sở hữu; 404 nếu thiếu Scan/ảnh hoặc đường
dẫn không an toàn. File chỉ nằm trong UPLOAD_DIR, JPEG/PNG. Response có
Cache-Control: private, no-store và X-Content-Type-Options: nosniff.
FE lấy bằng Authorization header, không đặt token vào URL, không public uploads.

## Kiểm chứng thực tế

- mypy: đạt, 81 source files.
- compileall app/tests: đạt.
- 8 kiểm tra schema độc lập: đạt (null, field ngoài schema, password yếu,
  field bỏ qua và null hợp lệ).
- Đã viết 10 regression cases trong tests/test_non_ml_completion.py.
- Chưa xác nhận integration tests đạt: PostgreSQL cấu hình 127.0.0.1:55432
  từ chối kết nối (TCP 10061). Đã dừng lượt pytest chờ; không đổi .env, không
  chuyển sang PostgreSQL service khác và không khởi động hạ tầng tự động.

Khi DB test đã sẵn sàng, chạy trong backend:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_non_ml_completion.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m mypy app tests scripts
```

Fixture tạo/xóa database có hậu tố _test. Chỉ dùng tên DB dành riêng cho test,
không chạy hai suite đồng thời trên cùng database. Suite mặc định không yêu cầu
tải thêm file ML; case audit ảnh thật là opt-in.

## Chưa triển khai trong lượt này

Khóa/mở tài khoản (cần chốt quyền và thêm migration), hoàn thiện inference_snapshot,
phân trang các danh sách còn lại, cập nhật ba Word, backup/restore thực nghiệm và
kiểm thử tải production. Các việc này không phụ thuộc file ML nhưng không được
coi là đã hoàn tất. Nhận diện lá/OOD/benchmark model vẫn hoãn theo yêu cầu.
