# Báo cáo rà soát và hoàn thiện Backend Tuần 1–4

Ngày kiểm tra: 04/09/2026

## 1. Kết luận

Backend Tuần 1–4 đã được rà soát lại theo contract API mới và hướng ba model.
Các flow Auth, Farm/Disease, Predict và Managed User/Farm Member/Scan đã được
nối end-to-end. Database hiện dùng migration head `f6a7b8c9d0e1`; bản DB trước
nâng cấp được giữ tại `backend/backups/plant_disease.before-multimodel-20260904.db`.

Ba classifier đều đã load strict và inference thật thành công:

- EfficientNet-B0: temperature `1.4939864873886108`;
- MobileNetV2: temperature `1.0`;
- ResNet50: temperature `1.4951273202896118`.

Không có artifact nào là leaf detector, segmentation hay OOD model. Vì vậy hệ
thống chỉ gọi phần hiện tại là **rejection baseline**, chưa tuyên bố “nhận diện
chắc chắn không phải lá”.

## 2. Tuần 1 — Auth foundation

### Đã bảo đảm

- Public register luôn hardcode `role=user`; schema từ chối field lạ nên gửi
  `role=admin` nhận 422.
- Mật khẩu đăng ký/cấp tài khoản tối thiểu 8 ký tự, có chữ hoa, chữ thường và số;
  hash bằng Argon2, không trả `password_hash` qua API.
- Access token 15 phút, refresh token 7 ngày trong HttpOnly cookie.
- Cả hai token có `token_version`, `iat`, `jti`, `type`; access có role.
- `/auth/me` chỉ nhận access token và so `token_version` với DB.
- `/auth/refresh` chỉ nhận refresh token và cũng so version với DB.
- `/auth/logout` tăng version, nên access/refresh cũ đều mất hiệu lực ngay.
- Race condition register trùng username/email được chặn thêm bằng xử lý
  `IntegrityError`, không để session lỗi hoặc trả stack trace.

### Tác dụng

`token_version` là cơ chế revoke toàn bộ phiên của một user mà không cần bảng
blacklist. Nó phù hợp logout, đổi mật khẩu hoặc khóa tài khoản. Đổi lại, logout
một thiết bị sẽ đăng xuất mọi thiết bị; đây là chủ ý hiện tại.

Refresh response tạo cookie mới nhưng refresh token cũ chưa phải one-time token,
vì không có bảng lưu `jti`/token family. Nếu cần chống replay tuyệt đối, bổ sung
refresh-token family ở giai đoạn hardening; không nên gọi cơ chế hiện tại là
rotation có phát hiện reuse.

## 3. Tuần 2 — Database, Farm, Disease Info và seed

### Đã bảo đảm

- Giữ các CHECK/FK/index nền tảng, gồm `idx_users_role`,
  `idx_users_created_by` và SQLite foreign key pragma.
- Farm là Manager-only; list/detail/update/delete đều kiểm tra ownership. Đã có
  `GET /farms/{id}` theo yêu cầu.
- Xóa Farm là soft-delete bằng `archived_at`, giữ liên kết Scan lịch sử.
- Disease Info public-read, Admin-only write; xóa bằng `is_active` để không phá
  nội dung lịch sử.
- Seed idempotent tạo 4 demo user, đủ 38 Disease Info và ba Model Version.
- Seed không ghi đè nội dung bệnh/Admin activation hiện có.
- Mỗi artifact được kiểm tra contract và SHA-256 trước khi đăng ký.

### Tác dụng

Soft-delete giúp thống kê/lịch sử không bị mất ngữ cảnh. Seed có thể chạy lại
an toàn trong demo/CI. Contract artifact chặn sớm các lỗi nguy hiểm như sai thứ
tự class, temperature không hợp lệ, thiếu trọng số hoặc giao nhầm kiến trúc.

Mật khẩu demo mặc định mới là `Demo123321!` và có thể đổi bằng
`SEED_DEMO_PASSWORD`. Seed không đổi mật khẩu record đã tồn tại.

## 4. Tuần 3 — Multi-model Predict

### Policy role/mode

| Actor | `auto` | Models |
|---|---|---|
| Guest | Basic | EfficientNet-B0 |
| User, Manager | Standard | EfficientNet-B0 + MobileNetV2 |
| Technician, Admin | Advanced | cả ba model |

`POST /predict` nhận `mode=auto|basic|standard|advanced`. Client được hạ mode
nhưng không được nâng quá role; server trả 403 nếu cố vượt quyền.
`GET /predict/capabilities` cho FE biết lựa chọn hợp lệ nhưng không thay thế
authorization phía server.

### Cách inference hoạt động

1. Query đúng active version cho từng `model_type`.
2. Lazy-load/cached model bằng `(model_version_id, sha256)` và strict state dict.
3. Dùng cùng preprocessing 224×224/ImageNet normalization.
4. Áp dụng `softmax(logits / temperature)` riêng từng model.
5. Chạy các model cùng mode bằng thread pool khi cấu hình parallel bật.
6. Lấy trung bình xác suất (equal-weight soft voting).
7. Tính confidence, Top1–Top2 margin, normalized entropy, JS divergence,
   agreement và energy score.
8. Chỉ trả label/Disease Info/treatment nếu rejection policy chấp nhận.

Advanced cần ít nhất hai model thành công; Basic/Standard cần ít nhất một.
Thiếu model nhưng còn đủ tối thiểu sẽ đánh dấu `degraded`; không đủ trả 503.

### Rejection baseline

Ngưỡng cấu hình ban đầu:

- ensemble confidence `< 0,3` → `low_confidence`;
- Top1–Top2 margin `< 0,05` → `ambiguous`;
- JS divergence `> 0,3` → `ambiguous`.

`ood_score=max(1-confidence, entropy, JS)` chỉ là tín hiệu tổng hợp để log và
phân tích. Temperature scaling làm probability bớt lệch calibration; nó không
biến classifier thành OOD detector.

Smoke test ảnh xanh trơn cho thấy lý do phải dùng nhiều tín hiệu: MobileNetV2
tự tin khoảng `0,995`, nhưng EfficientNet/ResNet rất khác; ensemble có
`JS≈0,482` và đã từ chối `ambiguous`. Một mẫu này không đủ đánh giá độ chính xác.

### Persistence

Guest không lưu DB/file. User đăng nhập lưu atomically:

- `scans`: kết quả/policy ensemble;
- `scan_topk`: Top-3 ensemble;
- `scan_model_results`: dự đoán, uncertainty, latency, lỗi và Top-K từng model;
- file ảnh UUID trong vùng upload.

Nếu DB lỗi, transaction rollback và ảnh vừa ghi bị xóa. Farm assignment được
kiểm tra theo ownership/membership; request vẫn có thể thành công với warning
và `farm_id=null` nếu Farm không hợp lệ.

## 5. Tuần 4 — Managed User, Farm Member và Scan ownership

### Đã bảo đảm

- Admin chỉ tạo `technician`/`manager` qua `/admin/users`.
- Manager request không có field role; service hardcode `user`.
- `created_by` ghi đúng người cấp tài khoản.
- Manager chỉ list User do chính mình tạo.
- Manager chỉ gán User do chính mình tạo vào Farm mình sở hữu.
- `(farm_id,user_id)` unique; membership mới ghi `added_by` để audit.
- Xóa membership không xóa User.
- `/scans/history`, `/scans/{id}` và DELETE đều owner-only cho mọi role;
  Admin không được xem scan người khác qua API User.
- Scan detail trả Top-3 ensemble và audit model; delete cascade cả hai tập kết quả
  rồi dọn ảnh.

### Tác dụng

Hai lớp `created_by` và Farm ownership ngăn Manager chiếm User/Farm của Manager
khác. `added_by` trả lời được ai đã thực hiện việc phân công. Tách quyền Admin
khỏi API owner-only tránh “Admin mặc định bypass mọi nghiệp vụ”; `/admin/scans`
sẽ là API giám sát riêng ở tuần sau.

## 6. Database mới

| Bảng | Vai trò |
|---|---|
| `users` | tài khoản, role, creator, token revoke version |
| `farms` | Farm thuộc Manager, soft-delete |
| `farm_members` | Managed User trong Farm, unique + `added_by` audit |
| `disease_info` | nội dung bệnh theo label, soft-delete |
| `model_versions` | artifact/calibration/metrics metadata theo kiến trúc |
| `scans` | kết quả ensemble và trạng thái rejection/agreement |
| `scan_topk` | Top-3 ensemble |
| `scan_model_results` | kết quả chi tiết mỗi model trong một Scan |

Partial unique index mới là:

```text
UNIQUE(model_type) WHERE is_active = 1
```

Vì vậy ba type có thể cùng active, nhưng hai EfficientNet active đồng thời bị
DB từ chối. Cột chuỗi `scans.model_version` cũ được giữ tạm để client/lịch sử
cũ không hỏng; `primary_model_version_id` và bảng per-model là nguồn mới.

## 7. API Tuần 1–4 sau hiệu chỉnh

- Auth: register, login, refresh, me, logout.
- Predict: POST `/predict`, GET `/predict/capabilities`.
- Farms: POST/GET `/farms`, GET/PUT/DELETE `/farms/{farm_id}`.
- Farm Members: POST/GET `/farms/{farm_id}/members`, DELETE member.
- Disease Info: public GET list/detail, Admin POST/PUT/DELETE.
- Admin Users: POST/GET `/admin/users`.
- Manager Users: POST/GET `/manager/users`.
- Scans: GET history/detail, DELETE owner-only.

Các API Proposal, Admin Scans, Stats, Explainability và Model Operations chưa
thuộc deliverable Tuần 1–4 và không được đánh dấu hoàn thành.

## 8. Rủi ro còn lại và bước tiếp theo

1. **OOD chưa được đo:** cần tập negative/near-OOD, AUROC/FPR95, threshold report.
2. **Ba model có thể học lỗi giống nhau:** ensemble không thay thế dữ liệu thực địa.
3. **CPU/RAM:** ResNet50 lớn; benchmark concurrency, RAM peak và queue/backpressure.
4. **Thread parallelism:** có thể nhanh hơn ở một request nhưng giảm throughput
   khi nhiều request; phải load-test trước khi bật production.
5. **Artifact delivery:** `*.pt` bị Git ignore; deployment phải mount/copy đúng
   file và chạy seed/verification.
6. **Activation API:** Tuần 6 cần validate, warm-up rồi đổi active version cùng
   type trong một transaction; không được tắt model type khác.
7. **Paywall:** nếu triển khai, tạo entitlement/subscription server-side; không
   dùng role hoặc cờ client làm bằng chứng đã trả phí.
8. **Refresh replay:** token cũ còn dùng được tới logout/version bump; cân nhắc
   token-family nếu phạm vi bảo mật yêu cầu.

Bước hợp lý tiếp theo là đóng ML acceptance contract và tập OOD, rồi mới làm
Grad-CAM/Proposal Tuần 5. Grad-CAM phải gắn với một model result cụ thể vì
ensemble không có một feature map chung.
