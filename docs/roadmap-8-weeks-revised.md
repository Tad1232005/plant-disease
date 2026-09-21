# Roadmap 8 tuần đã hiệu chỉnh — Plant Disease Detection

## 1. Phạm vi và giả định

- Nhóm 3 người, thời lượng 8 tuần, mục tiêu là đồ án học phần có demo ổn định.
- SQLite và local file storage được chấp nhận cho một deployment đơn/ demo;
  không tuyên bố đây là kiến trúc production nhiều instance.
- Có 4 role lưu trong DB: `user`, `technician`, `manager`, `admin`.
- Guest là trạng thái chưa đăng nhập; Managed User là `role=user` có
  `created_by`, không phải hai role mới.
- Ưu tiên cao nhất là một vertical slice chạy thật từ ảnh → inference → lưu
  lịch sử → tra cứu → dashboard, sau đó mới thêm chức năng quản trị mở rộng.

## 2. Trạng thái hiện tại

| Khối | Trạng thái | Ghi chú |
|---|---|---|
| Auth/JWT/RBAC | Hoàn thành | Access/refresh, token_version, logout revoke |
| Schema nền tảng | Hoàn thành | 8 bảng; thêm FarmMember và ScanModelResult audit |
| Farm/Disease CRUD + seed | Hoàn thành | Manager-only Farm; Disease write Admin-only |
| Managed User/Farm Member | Hoàn thành backend | Migration, ownership, regression privilege escalation |
| Scan history/detail/delete | Hoàn thành backend | Owner-only, đã nối với Scan tạo bởi Predict thật |
| Inference API | Hoàn thành backend | 1/2/3 model theo role, calibrated soft-voting, persistence, cleanup |
| ML baseline | Đã tích hợp 3 artifact | EfficientNet-B0, MobileNetV2, ResNet50; chưa có model card/metrics được bàn giao |
| OOD/Calibration | Baseline kỹ thuật | Đã dùng temperature + confidence/margin/JS; chưa có tập OOD và threshold report |
| Grad-CAM | Chưa hoàn thành | Chưa có pipeline/API/artifact |
| Proposals/Stats/Admin scans/Model API | Chưa hoàn thành | Registry DB đã dùng thật; API quản trị/activate để Tuần 6 |
| Frontend | Mới ở mức upload/result | Chưa có auth, role UI, history, farm, dashboard, workflow |
| CI/Deployment/E2E | Chưa rõ/chưa hoàn thành | Cần gate trước tuần cuối |

## 3. Các quyết định thiết kế bắt buộc

### 3.1 Quyền Admin không đồng nghĩa dùng mọi API của role khác

Admin có quyền kiểm soát hệ thống qua API riêng, không bypass ownership của
Manager/User:

- `/farms/*`: chỉ Manager sở hữu được thao tác.
- `/scans/*`: tài khoản hiện tại chỉ thấy scan của mình.
- `/admin/scans`: Admin giám sát toàn hệ thống.
- `/stats/farm/*`: Manager sở hữu.
- `/stats/admin/*`: Admin giám sát toàn hệ thống.
- Grad-CAM: Technician/Manager theo quyết định nghiệp vụ, không mặc định Admin.

Xóa câu “Admin có toàn quyền trên mọi module” khỏi tài liệu. Thay bằng “Admin
có toàn quyền trên các module kiểm soát hệ thống được thiết kế cho Admin”.

### 3.2 Luồng Predict phải là nguồn tạo Scan

`POST /predict` dùng optional authentication:

- Guest: inference và trả kết quả; không ghi DB, không nhận `farm_id`.
- User đã đăng nhập: lưu ảnh, `scans`, `scan_topk`, model version.
- Managed User: chỉ gắn `farm_id` nếu tồn tại membership.
- Manager: chỉ gắn Farm do mình sở hữu.
- User thường/Technician/Admin: không gắn Farm.

Nếu Farm không hợp lệ, không được âm thầm bỏ qua. Scan có thể vẫn thành công với
`farm_id=null`, nhưng response phải có warning có cấu trúc như
`farm_assignment_status="not_allowed"`.

Toàn bộ thao tác ghi Scan + TopK phải nằm trong một transaction. Nếu lưu DB
thất bại, dọn file ảnh vừa tạo hoặc đánh dấu orphan để cleanup.

### 3.3 OOD không dùng mỗi max-softmax để khẳng định “không phải lá”

PlantVillage chỉ chứa lá/cây trong điều kiện khá sạch. Max softmax có thể vẫn
cao trên ảnh người, đồ vật hoặc nền lạ. Phải đổi ngôn ngữ sản phẩm từ
“phát hiện chắc chắn ảnh không phải lá” thành “ảnh ngoài phân phối/độ tin cậy
không đủ”.

Mức tối thiểu cho đồ án:

1. Tạo tập negative/OOD riêng gồm đồ vật, người, đất, bầu trời, ảnh mờ.
2. Đánh giá AUROC/FPR95 hoặc ít nhất precision/recall tại threshold chọn trước.
3. Calibration trên validation set (temperature scaling hoặc phương án tương
   đương), không chọn threshold bằng test set.
4. UI hiển thị cảnh báo, không đưa khuyến nghị điều trị khi ảnh bị invalid.

Nếu không đủ thời gian, gọi tính năng là “low-confidence rejection”, không gọi
là OOD detection hoàn chỉnh.

### 3.4 Disease proposal không tự biến thành class mới của model

Model chỉ dự đoán các label có trong `classes.json`. Vì vậy:

- Proposal sửa nội dung của label hiện có: có thể approve vào `disease_info`.
- Proposal tạo label mới: chuyển trạng thái `needs_retraining`; không public và
  không được coi là model đã nhận diện được label đó.
- Chỉ public label mới khi một Model Version chứa label đó được validate và
  activate.

### 3.5 Model Version điều khiển inference thật, activate vẫn cần transaction

Inference hiện truy vấn version active theo từng `model_type`, load đúng file/
classes/temperature và cache theo `(id, sha256)`. Partial unique index đảm bảo
mỗi type chỉ có tối đa một version active; ba type khác nhau được active song
song.

Khi activate cần:

- kiểm tra manifest/checksum, file tồn tại và load được;
- kiểm tra số output khớp `classes.json`;
- warm-up inference;
- activate version mới và deactivate version cũ cùng `model_type` trong một
  transaction; cache key mới giúp request sau load artifact mới;
- rollback active version nếu load thất bại.

API quản trị activate chưa thuộc Tuần 1–4, vì vậy hiện activation được seed/
migration quản lý; không tuyên bố đã có hot-swap qua API.

### 3.6 Giữ tính toàn vẹn dữ liệu lịch sử

- Farm có dashboard lịch sử: đã dùng `soft delete` (`archived_at`) thay vì xóa
  cứng làm `scans.farm_id` thành NULL.
- Disease Info đã được scan tham chiếu: đã dùng `is_active`; API public ẩn nội
  dung đã xóa nhưng chi tiết Scan lịch sử vẫn tra cứu tên bệnh và điều trị.
- DELETE Scan xóa DB/top-k; quyết định rõ retention của ảnh và Grad-CAM artifact.

## 4. Phạm vi ưu tiên

### P0 — Bắt buộc để bảo vệ/demo

- Inference ảnh thật, confidence/top-3, low-confidence rejection có đánh giá.
- Guest và authenticated predict; lưu Scan/TopK đúng transaction.
- Auth, history owner-only, Disease Info public.
- Manager tạo Farm/User, gán Member; Managed User scan gắn Farm.
- Dashboard Farm cơ bản và Admin overview cơ bản.
- Frontend responsive cho flow demo chính.
- Test, deployment, seed, backup/demo data và tài liệu giới hạn mô hình.

### P1 — Làm khi P0 đã ổn định

- Grad-CAM cho Technician/Manager.
- Disease Proposal approval workflow.
- Camera capture.
- Admin scan monitoring và recent-invalid.

### P2 — Cắt trước nếu trễ tiến độ

- Hot activation nhiều Model Version.
- Dashboard nâng cao/xu hướng phức tạp.
- Thêm label bệnh mới qua workflow retraining hoàn chỉnh.
- UI quản trị quá chi tiết hoặc realtime.

## 5. Roadmap 8 tuần theo ba luồng song song

Mỗi tuần có một “exit gate”; không chuyển tuần nếu luồng cốt lõi của gate chưa
chạy end-to-end.

### Tuần 1 — Foundation và hợp đồng hệ thống — ĐÃ HOÀN THÀNH

**Backend:** FastAPI, config, Auth/JWT, refresh cookie, RBAC, token_version.

**Frontend:** skeleton, API client, route/layout cơ bản, thiết kế màn login.

**ML/QA:** khóa 38 class, format `classes.json`, baseline reproducible.

**Exit gate:** register/login/refresh/logout/me chạy và có test.

### Tuần 2 — Data foundation và public content — ĐÃ HOÀN THÀNH BACKEND

**Backend:** migrations, constraints/index, Farm CRUD, Disease Info CRUD, seed.

**Frontend:** public predict screen, result card, Disease Info display.

**ML/QA:** split theo leaf, baseline metrics, confusion matrix.

**Exit gate:** database sạch migrate+seed được; public content và Farm RBAC có
integration test.

### Tuần 3 — Multi-model inference vertical slice — BACKEND ĐÃ HOÀN THÀNH

**Backend:**

- harden upload (size, MIME thực, ảnh hỏng, timeout);
- artifact contract + checksum cho ba classifier;
- Basic (1), Standard (2), Advanced (3) theo role và chống mode escalation;
- temperature scaling, soft-voting, margin/entropy/JS disagreement;
- optional auth cho `/predict`;
- lưu ảnh/Scan/TopK/per-model result cho user đăng nhập;
- validate Farm theo member/owner và trả warning có cấu trúc;
- response nối Disease Info và các model version thực tế;
- transaction/cleanup khi lỗi.

**Frontend:** auth store, cookie refresh, upload/camera fallback, history/detail.

**ML/QA còn thiếu:** negative/OOD evaluation set, threshold report và model
card. Temperature đã tích hợp nhưng không thay thế OOD evaluation.

**Exit gate:** Guest scan không tạo DB; User scan tạo đúng 1 Scan + TopK; Managed
User gắn đúng Farm; farm sai không được ghi; mode vượt quyền bị 403; E2E từ UI
chạy được.

### Tuần 4 — Organization và ownership — BACKEND ĐÃ HOÀN THÀNH VÀ TÍCH HỢP

**Backend:** Admin Users, Manager Users, Farm Members có `added_by`, scan
history/detail/delete kèm audit từng model.

**Frontend:** màn quản lý Farm, Managed User và Member; history owner-only.

**Security:** Manager gửi `role=admin` bị 422 và không có record được tạo.

**Exit gate:** Admin → Manager → 2 Managed User → Farm → 2 members chạy thật.

Phần Scan đã được kiểm thử bằng nguồn ghi từ Predict, không còn chỉ dùng fixture.

### Tuần 5 — Explainability và content governance

**Backend/ML:**

- Grad-CAM artifact và authorization;
- explanation phải chọn một `scan_model_result`/`model_type` cụ thể vì ensemble
  không có một feature map chung; cấu hình target layer riêng cho từng kiến trúc;
- không dùng GET để sinh artifact: dùng `POST /scans/{id}/explanation` để tạo,
  `GET /scans/{id}/explanation` để đọc;
- Disease Proposal create/mine/admin review/approve/reject;
- proposal label mới đi `needs_retraining`.

**Frontend:** Grad-CAM viewer, proposal form, mine queue và Admin review.

**Exit gate:** Technician đề xuất sửa label hiện có → Admin approve → Guest thấy
nội dung mới; unauthorized role không sinh/xem Grad-CAM.

### Tuần 6 — Analytics, monitoring và model operations

**Backend:**

- Manager Farm stats có ownership;
- Admin overview/recent-invalid và `/admin/scans` có filter/pagination;
- query theo khoảng thời gian, index và query-plan kiểm tra;
- Model Version API: list/register/activate theo `model_type`; activate có
  validate + warm-up + transaction rollback, không tắt hai model type còn lại;
- entitlement/paywall nếu làm thật phải là capability server-side riêng, không
  suy luận trực tiếp từ role và không tin cờ do client gửi;
- hiệu chỉnh threshold từ tập ID/OOD; version hóa `policy_version` để số liệu
  lịch sử giải thích được.

**Frontend:** dashboard Manager/Admin, filter và empty/error state.

**ML/QA:** model card, giới hạn dataset, benchmark CPU latency/memory.

**Exit gate:** dashboard số liệu khớp fixture SQL; Admin API tách khỏi User/Manager
API; không có query toàn bảng không giới hạn.

### Tuần 7 — Feature freeze và tích hợp sản phẩm

- Dừng thêm chức năng mới giữa tuần.
- Hoàn thiện responsive/camera/accessibility/loading/error/refresh-token flow.
- E2E theo 6 actor types: Guest, independent User, Managed User, Technician,
  Manager, Admin.
- CI chạy backend test, frontend build/lint và migration check.
- Deploy staging; quyết định persistent volume cho DB/uploads hoặc chuyển dịch vụ
  lưu trữ nếu thực sự cần.

**Exit gate:** staging chạy toàn bộ demo script; không còn bug P0/P1.

### Tuần 8 — Hardening, báo cáo và bảo vệ

- Chỉ sửa bug; không thêm scope.
- Security pass: upload abuse, IDOR, role escalation, cookie/CORS, secrets.
- Backup/restore database, seed demo deterministic, log không lộ token/password.
- Kiểm thử trên ảnh ngoài PlantVillage và ghi rõ failure cases.
- Chuẩn bị video dự phòng, slide kiến trúc, model card, risk register và kịch bản
  demo khép kín.

**Exit gate:** release candidate có tag, deploy tái tạo được từ README, demo offline
fallback sẵn sàng.

## 6. Kế hoạch phục hồi từ tiến độ hiện tại

Vì Backend Tuần 4 đã làm trước Inference vertical slice Tuần 3, thứ tự tiếp theo
không nên là làm ngay Proposal/Stats. Thứ tự phục hồi:

1. Backend Tuần 3 đã hoàn tất; ML còn tập negative/OOD, threshold report và
   metrics/model card cho từng model.
2. Song song, một thành viên bắt kịp Frontend Tuần 1-4.
3. E2E backend Tuần 4 trên Scan tạo bởi API thật đã hoàn tất; FE cần nối contract.
4. Sau đó mới bắt đầu Tuần 5.
5. Cuối Tuần 6 đánh giá scope; cắt P2 ngay nếu frontend hoặc real-world ML trễ.

## 7. Definition of Done chung

Một chức năng chỉ được đánh dấu hoàn thành khi có đủ:

- migration/schema (nếu cần) và downgrade hợp lệ;
- authorization/ownership ở service, không chỉ ẩn nút frontend;
- happy path, validation, forbidden, not-found và conflict test;
- OpenAPI/request/response ổn định;
- UI loading/empty/error state;
- tài liệu chạy và seed/fixture;
- test trên staging hoặc E2E qua HTTP thật;
- giới hạn và failure mode được ghi trong báo cáo.
