# Bổ sung backend vận hành — tuần 8

Ngày 16/09/2026. Phạm vi: backend, không sửa frontend, thư mục ml, trọng số,
temperature, thuật toán/ngưỡng inference. Người dùng đã chọn **chưa nâng DB
ứng dụng, tiếp tục code và test**. Không sửa `.env`, không backup/migrate dữ liệu
ứng dụng, không tạo tài khoản thật, không commit/tag hay triển khai production.

## 1. Những gì thực hiện trong đợt này

| Phần | Cách làm | Tác dụng và ảnh hưởng |
| --- | --- | --- |
| Settings | Thêm APP_ENV, PUBLIC_API_ORIGIN; validation production cho secret, HTTPS origin, Secure Cookie, DB credential; giới hạn số dương cho pool/upload/timeout/TTL | Fail sớm khi cấu hình sai thay vì chạy với cấu hình không an toàn. Development vẫn là mặc định, không tự thay .env |
| Auth browser | Dependency kiểm tra Origin trên request Auth không phải GET/HEAD/OPTIONS; chặn Origin lạ/null/trùng và cross-site Fetch Metadata thiếu Origin | Bổ sung bảo vệ cho endpoint đặt/đọc cookie. CORS không còn là lớp kiểm tra duy nhất. CLI không Origin vẫn dùng được; FE domain phải khai báo đúng |
| HTTP headers | Auth response no-store/no-cache; thêm X-Content-Type-Options nosniff | Giảm nguy cơ cache response chứa token và MIME sniffing; không đổi payload JSON |
| Alembic | Escape `%` trước khi URL đi qua ConfigParser | Mật khẩu có ký tự đặc biệt được URL-encode không gây lỗi interpolation; không đổi revision |
| Preflight | CLI chỉ đọc với timeout, kiểm DB/head/bảng/cột, quyền role và quyền truy cập uploads; có --config-only | Phát hiện DB lạc schema trước vận hành, không in credential hay tự sửa dữ liệu |
| Bootstrap Admin | CLI terminal nhập password ẩn hai lần, transaction + advisory lock + audit | Tạo Admin đầu tiên mà không cần model/demo seed. Không nâng role/reset account hiện hữu, không tạo Admin thứ hai |
| Demo seed | Chặn seed_week2 khi APP_ENV=production trước khi đọc artifacts | Tránh tạo tài khoản/mật khẩu demo trong môi trường thật; dev seed cũ được giữ |
| Docker | Python 3.12; torch 2.13.0+cpu, torchvision 0.28.0+cpu; user 10001, healthcheck, single worker, không tự migrate | Build và chạy được backend CPU, tránh phụ thuộc CUDA; không thay phiên bản thư viện trong venv local hay file model |
| Compose | API-only, dùng .env hiện có, DB quản lý riêng, uploads volume riêng, model mount read-only, rootfs read-only, cap_drop/no-new-privileges | Chuẩn bị cách chạy tách code/secrets/dữ liệu. Không phải lệnh tự chuyển DB/ảnh hiện tại vào container |

File chính: `app/core/config.py`, `app/api/auth_origin.py`, `app/main.py`,
`alembic/env.py`, `scripts/preflight.py`, `scripts/bootstrap_admin.py`,
`Dockerfile`, `compose.backend.yml`, `tests/test_deployment_readiness.py`.

## 2. Kết quả kiểm thử cuối cùng

- **212 passed, 1 deselected, 2 warnings, 119,79 giây**. Tăng 37 test so với
  bộ 175 test tuần 7. Đây là lượt chạy sau các thay đổi cuối của code/test.
- Bỏ file test ảnh thật và deselect real_artifact_contract theo phạm vi.
  Không kiểm chứng accuracy/OOD/nhận diện lá bằng kết quả này. Một số test seed
  cũ vẫn đọc bundle có sẵn để kiểm metadata; không chạy inference ảnh thật.
- PostgreSQL test **17 trong Docker**, bind localhost:55439, data tmpfs riêng;
  client pg_dump/pg_restore **18**. Có đặt PG_BIN: test backup/restore thật chạy,
  không skip. Không trỏ bộ pytest vào DB ứng dụng.
- Mypy đạt **105 source files**; compileall và pip check đạt.
- `export_contract --check` đạt; API vẫn **41 thao tác nghiệp vụ**, snapshot
  OpenAPI `1.1.0-rc.1`, head `c9d0e1f2a3b4`, không thêm migration/API nghiệp vụ.
- Hai warning cũ: Starlette/httpx và passlib/argon2, chưa đổi dependency để xử lý.

Các test mới gồm cấu hình sai/production, che input credential trong error/repr,
preflight không ghi DB, DB unreachable/schema thiếu/cột thiếu, Origin hợp lệ/lạ,
Auth không cache, bootstrap đầu tiên/chống nâng role/audit rollback, hai bootstrap
đồng thời chỉ một Admin, chặn demo seed production và Alembic password URL-encode.

## 3. Docker và HTTP thật

Lượt build đầu phát hiện pip kéo CUDA dependencies từ torch wheel mặc định.
Đã chủ động hủy lượt đó và chuyển riêng Docker sang wheel CPU chính thức, giữ
đúng version đang dùng. Build CPU hoàn tất; pip check trong image đạt.

Image được giữ lại: **plant-disease-backend:week8-check**.
Docker inspect báo Size **368.987.512 byte**; đây là số do Docker cung cấp cho
image, không phải RAM chạy model hay tổng disk cache build. Base Python image
và build cache cũng còn để lần build sau tái sử dụng; không chạy global prune.

Kiểm chứng runtime Linux container:

- Chạy UID **10001**, rootfs read-only, dropped capabilities, no-new-privileges.
- Không có `/app/.env`, không có file `.pt` trong image.
- `torch.__version__ = 2.13.0+cpu`, `torch.version.cuda = None`.
- Named volume uploads riêng: ghi/đọc/xóa file giả thành công dưới UID 10001.
- Toàn bộ migration từ DB rỗng lên head chạy thành công trong container test.
- Preflight DB/head/bảng/cột/uploads đạt; cảnh báo đúng về test mode và DB
  superuser thử nghiệm. Đây không phải cấu hình DB role production được nghiệm thu.
- Docker health status **healthy**; healthcheck vẫn chỉ DB/schema, không model.
- CLI bootstrap tương tác thực: nhập ẩn hai lần, tạo đúng Admin giả trong DB test.
- **17 kiểm tra HTTP thật** trên localhost:58017 đạt: liveness/readiness, disease
  list, capabilities, chặn login Origin lạ, login/me/refresh, Admin không được
  Farm CRUD, Admin tạo Manager, Manager tạo/xem Farm, stats Farm/Admin, logout
  và access token cũ bị 401. Không gọi Predict inference.

Không chạy `docker compose up` trỏ vào DB thật. Compose được validate bằng
`config --quiet`; runtime được test bằng container/network/volume tách biệt với
các tùy chọn bảo vệ tương ứng. Container không có model nên không kết luận
Predict, Grad-CAM, CPU accuracy, HTTPS hay FE browser đã hoạt động đầy đủ.

## 4. Phát hiện trên DB ứng dụng (chỉ đọc)

Preflight thực tế xác nhận:

| Kiểm tra | Kết quả |
| --- | --- |
| Kết nối DB | Đạt |
| Revision | b8c9d0e1f2a3, chưa lên c9d0e1f2a3b4 |
| Bảng thiếu | audit_events, disease_proposals |
| Cột thiếu | users.status, disease_info.content_version |
| Upload directory | Truy cập được; chưa thử ghi file thật |
| Runtime DB role | Cảnh báo quyền cao |
| Environment | Development, chưa áp guard production |

**DB thật giữ nguyên theo xác nhận người dùng.** Vì vậy API code mới chưa thể
nghiệm thu trên DB đó dù regression/container test đạt. Không sửa lỗi thiếu
schema bằng create_all, stamp giả revision hay tự tạo bảng trong pgAdmin.

## 5. Cleanup và việc còn lại

Đã dừng/xóa hai container test, network test, named volume test và cluster
PostgreSQL tạm chưa sử dụng trên Windows. Chỉ dữ liệu giả được xóa; có thể tạo
lại qua test. Không còn API/DB test chạy từ lượt này. Image/build cache được giữ.

Chưa hoàn thành/không làm trong đợt này:

1. Backup nhất quán rồi migrate **DB ứng dụng** sau khi người dùng xác nhận
   maintenance window; smoke trên DB ứng dụng đã nâng.
2. Domain/TLS, reverse proxy, role DB ít quyền, ingress rate limit, disk quota,
   retention/rotation và restore dữ liệu đại diện quy mô thật.
3. Browser E2E với người phụ trách FE; FE cần đúng origins, không cần custom
   header mới. Tài liệu handoff backend đã cập nhật, không sửa code FE.
4. Toàn bộ việc model/OOD/leaf detection/Grad-CAM/registry còn hoãn như báo cáo
   trước; không tự công bố is_valid_leaf là chứng minh ảnh lá.
5. Cập nhật ba Word cũ, review rồi commit/tag release; chưa làm trong lượt này.

Hướng dẫn thao tác chi tiết: [DEPLOYMENT.md](DEPLOYMENT.md).
