# Tuần 7 — tích hợp và chuẩn bị bàn giao backend

> Cập nhật tiếp theo: [báo cáo tuần 8](../week8/REPORT.md) đã có kết quả build
> và chạy container thử, preflight và bootstrap Admin. Những mục bên dưới là
> kết quả tại mốc tuần 7, không thay thế báo cáo mới.

Ngày: 16/09/2026. Phạm vi vẫn chỉ backend, không đổi frontend/ml/artifact.
API candidate: **1.1.0-rc.1**. Schema head giữ **c9d0e1f2a3b4**, không có migration
mới của tuần 7. Chưa tạo Git tag/commit phát hành hay triển khai production.

## 1. Đối chiếu roadmap

| Ngày | Backend đã thực hiện | Chưa được coi là hoàn thành |
| --- | --- | --- |
| 1 | Snapshot OpenAPI, kiểm tra drift, mô tả lỗi/cookie/phân trang và handoff FE | FE build, browser smoke và hai bên ký nhận contract |
| 2 | Kịch bản API xuyên suốt 6 nhóm người dùng, auth/DB thật và test quyền | Browser E2E hoặc kết quả ảnh thật; inference dùng fixture |
| 3 | Công cụ benchmark HTTP giới hạn, chỉ đọc, ghi p50/p95/RSS và lỗi | Benchmark Predict/model, tải production, reverse proxy/TLS |
| 4 | Backup DB+uploads, restore DB mới, so count/hash và mở ảnh qua API | Backup dữ liệu thật và model bundle, RPO/RTO production |
| 5 | Chốt contract ứng viên, chạy regression và ghi rõ giới hạn | Bản phát hành được nghiệm thu đầy đủ FE/ML/deploy |

## 2. Các thay đổi

### Contract và health

- `scripts/export_contract.py`: export/check OpenAPI. Test fail khi contract
  khác code. [Bản JSON](openapi.json) và [hướng dẫn FE](FRONTEND_HANDOFF.md).
- Bổ sung schema lỗi có detail chuỗi hoặc danh sách validation, không đổi
  payload lỗi hiện có. HTTP status vẫn do các route/service quyết định.
- `GET /health/live` và `/health/ready` là endpoint vận hành ngoài 41 API nghiệp vụ.
  Readiness dùng kết nối DB riêng có timeout, kiểm migration head; không load
  model và không công bố readiness toàn bộ Predict.
- Bỏ credentials mẫu khỏi alembic.ini; URL thực vẫn lấy từ settings/.env.
  Bổ sung path_separator để bỏ cảnh báo cấu hình Alembic cũ.
- Không thay ngưỡng dự đoán, role matrix hoặc business schema.
- Dockerfile dùng Python 3.12 cùng major/minor môi trường test. Siết .dockerignore
  chặn .env, venv, backup, ảnh người dùng và trọng số khỏi build context. Model/ảnh
  phải cung cấp qua runtime storage, không nhúng bí mật vào image. Chưa build
  hoặc chạy Docker image; đây là chỉnh cấu hình, không phải chứng nhận container.

### Kiểm thử xuyên suốt

`test_week7_contract_e2e.py` đi qua Guest, User tự đăng ký, Admin cấp tài khoản,
Manager tạo 2 Managed User/Farm/members, Managed User tạo Scan, ảnh riêng và ảnh
giám sát, stats, Technician gửi đề xuất, Admin duyệt và khóa tài khoản. Các bước
login dùng password/JWT thật, không override RBAC; chỉ inference được giả lập.
Có test CORS preflight origin cho phép/bị từ chối và hai dạng error detail.

### Benchmark HTTP

`scripts/benchmark_http.py` chỉ cho localhost, HTTP, root URL, không credential
trong URL; giới hạn tối đa 5000 request/32 concurrent/timeout 60 giây.
Không ghi dữ liệu và không gọi POST Predict. Chỉ GET liveness, readiness,
danh sách disease-info limit 10 và capabilities. Không follow redirect hoặc
đọc proxy config môi trường. Warmup phải đủ 200 trước khi bắt đầu đo.

Ví dụ với Uvicorn local đã sẵn sàng, schema đã migrate:

```powershell
.\.venv\Scripts\python.exe -m scripts.benchmark_http --base-url http://127.0.0.1:8000 --requests 200 --concurrency 4 --timeout 5 --server-pid <PID_UVICORN> --output benchmark-results/run-01.json
```

Lấy PID từ dòng Started server process trong log Uvicorn, không lấy nhầm launcher
Python trên Windows. `sampled_peak_bytes` là mẫu RSS/working-set của đúng PID,
không phải peak chính xác và không gồm PostgreSQL/worker khác. Không đủ quyền
đọc RAM thì trả null; không ngụy tạo số 0. p50/p95 tính cả attempt lỗi/timeout.
Report luôn ghi scope/limitations, không dùng để cam kết tải production.

## 3. Backup/restore an toàn

`scripts/backup_restore.py` dùng pg_dump custom format, không nhận password qua
command line; subprocess lấy credentials từ môi trường riêng. Không backup
.env hay model bundle. Bản dump chứa dữ liệu nhạy cảm (kể cả hash mật khẩu):
đặt ở storage có quyền hạn chế, mã hóa/copy ra nơi an toàn theo chính sách triển
khai. Các thư mục backup mặc định đã được Git ignore; không commit bundle.

### Tạo backup

1. Dừng **tất cả** API worker/job ghi dữ liệu và chờ request đang chạy kết thúc;
   PostgreSQL vẫn phải hoạt động. CLI không tự dừng ứng dụng thay người vận hành.
2. Xác nhận .env trỏ đúng nguồn cần sao lưu. Chọn pg_dump cùng major với server
   hoặc client mới hơn có hỗ trợ; lượt diễn tập dùng PostgreSQL/client 18.
3. Chạy trong backend, chọn output chưa tồn tại:

```powershell
.\.venv\Scripts\python.exe -m scripts.backup_restore --pg-bin "C:\Program Files\PostgreSQL\18\bin" backup --output backups\offline-20260916 --writers-stopped
```

Bundle gồm database.dump, uploads và manifest.json. Manifest chỉ xuất hiện sau
khi dump/copy/kiểm tra xong. So sánh DB/file trước và sau để phát hiện thay đổi,
nhưng KHÔNG thay thế điều kiện dừng writers. Từ chối Scan thiếu ảnh, đường dẫn
không hỗ trợ, symlink, file không phải JPEG/PNG, output đã tồn tại hoặc chồng lên
uploads. File .tmp còn lại cần được kiểm tra riêng trước backup.

### Diễn tập restore

```powershell
.\.venv\Scripts\python.exe -m scripts.backup_restore --pg-bin "C:\Program Files\PostgreSQL\18\bin" restore --bundle backups\offline-20260916 --database plant_drill_restore_test --uploads storage\restore-drill-20260916
```

- Chỉ nhận tên DB mới hậu tố `_restore_test`; từ chối DB nguồn hoặc DB có sẵn.
- Thư mục ảnh đích phải mới, tách khỏi uploads ứng dụng và bundle.
- Không terminate session, DROP database, --clean hoặc ghi đè dữ liệu hiện hữu.
- Chỉ dùng bundle nguồn tin cậy do mình tạo. Hash phát hiện hỏng dữ liệu, không
  chứng minh backup được ký xác thực; pg_restore có thể thực thi SQL trong dump.
- Restore trong một transaction; xác minh mọi bảng bằng count và SHA-256 nội
  dung row có thứ tự PK, revision và từng ảnh. Thất bại không được promote;
  DB/thư mục mới có thể được giữ lại để người vận hành kiểm tra.
- Không tự migrate bản restore hoặc đổi .env. Nếu muốn chạy API kiểm tra,
  dùng tiến trình riêng có DATABASE_URL/UPLOAD_DIR trỏ clone, không trỏ DB thật.
- CLI chỉ diễn tập sang DB mới. Quyết định chuyển traffic sang bản phục hồi
  phải được người vận hành xác nhận riêng, không có chế độ tự ghi đè production.

### Bằng chứng diễn tập

[restore-verification.json](restore-verification.json): dataset synthetic,
không phải dữ liệu người dùng. Bao gồm dữ liệu User/Disease/Scan và một ảnh PNG.
So hash dữ liệu, ảnh, revision; mở lại ảnh qua owner-only API trả 200; đăng ký
User mới sau restore xác minh sequence không bị trùng; nguồn không đổi.
Các bảng khác được xác minh ở trạng thái rỗng; chưa chứng minh quy mô lớn hoặc
khôi phục artifacts/model. Test riêng chặn dump/ảnh sửa, traversal, thiếu ảnh,
đích đã tồn tại và không xác nhận dừng writers.

## 4. Chạy lại kiểm thử

Yêu cầu PostgreSQL test và quyền CREATEDB. Fixture tạo/xóa các DB *_test; không
để dữ liệu thật trong các tên test hoặc chạy hai suite cùng tên DB.

```powershell
$env:PG_BIN = 'C:\Program Files\PostgreSQL\18\bin'
.\.venv\Scripts\python.exe -m pytest -q --ignore=tests/test_predict_downloaded_samples.py -k "not real_artifact_contract"
.\.venv\Scripts\python.exe -m mypy app tests scripts
.\.venv\Scripts\python.exe -m scripts.export_contract --check
```

Nếu không đặt PG_BIN, test restore thực sẽ **skip**, không được báo là đã chạy.
Các test model artifact và ảnh trọng số thật tiếp tục bị loại trừ theo phạm vi.
Không cộng test phần mềm thành bằng chứng accuracy hoặc khả năng nhận diện lá.

## 5. Kết quả và giới hạn

**Kết quả cuối: 175 passed, 1 deselected, 150,09 giây.** File test ảnh chạy trọng
số thật bị ignore; kiểm artifact thật bị deselect theo phạm vi. Không có test
restore bị skip vì đã đặt PG_BIN. Có hai warning dependency Starlette/httpx và
argon2/passlib; chưa nâng dependency trong đợt đóng phạm vi này.

Mypy đạt **101 source files**, compileall đạt, `export_contract --check` đạt và
git diff whitespace check đạt. Tuần 7 bổ sung 27 test so với bộ 148 test trước.
Fixtures JSON FE được kiểm tra bằng response schemas, timeout/HTTP 503 của công
cụ đo được kiểm tra bằng transport giả; kết quả HTTP thật nằm ở report riêng.
Lượt nối lại từng lỗi setup vì server thử đã dừng/đang recovery; các lượt đó
không được tính là test đạt. Kết quả trên là lượt chạy hoàn chỉnh sau recovery.

[http-baseline.json](http-baseline.json): Uvicorn thật, 1 worker, Windows AMD64,
8 CPU logic, Python 3.12.0; DB chứa 20 nội dung bệnh synthetic, không load trọng
số. 200 request, concurrency 4, timeout 5 giây, thêm 4 warmup ngoài số đo.
**200/200 HTTP 200**, khoảng 1,74 giây, ~115 request/giây trong riêng lượt thử ngắn này.

| Route | p50 (ms) | p95 (ms) |
| --- | ---: | ---: |
| /health/live | 6,35 | 11,67 |
| /health/ready | 96,62 | 200,95 |
| /api/v1/disease-info?limit=10 | 12,51 | 16,48 |
| /api/v1/predict/capabilities | 7,95 | 13,12 |

RAM working-set cao nhất trong 3 mẫu: 268.914.688 byte (~256 MiB), chỉ PID
Uvicorn, không gồm PostgreSQL. Readiness chậm hơn vì dùng kết nối DB riêng.
Không suy ra các con số này cho login/ghi DB/Predict, tải lâu dài hoặc server
production. Không thiết lập SLA bằng một lượt baseline ngắn.

**DB ứng dụng chưa được migrate, không thay .env.** Backend mới vẫn cần head
c9d0e1f2a3b4 trước khi chạy. Restore/HTTP server của lượt này dùng DB riêng trên
localhost, không gửi dữ liệu ra dịch vụ ngoài. Không đụng thư mục FE/ml.
Sau nghiệm chứng đã dừng Uvicorn thử và dừng/xóa cluster PostgreSQL tạm riêng
của lượt này. Báo cáo JSON/OpenAPI được giữ trong docs/week7; DB ứng dụng không
bị xóa hoặc thay đổi. Muốn chạy lại cần khởi động server test mới theo hướng dẫn.

## 6. Điều kiện trước tuần 8/phát hành

- Người phụ trách FE chạy checklist handoff trên frontend thật và xác nhận.
- Backup DB ứng dụng, migrate schema, kiểm tra trên môi trường tích hợp.
- Nghiệm thu cấu hình HTTPS/cookie/CORS/secret, phân quyền filesystem và storage.
- Diễn tập backup dữ liệu đại diện quy mô thực, retention/mã hóa và RPO/RTO.
- ML/model/OOD/Grad-CAM/benchmark Predict vẫn hoãn; ghi rõ giới hạn sản phẩm.
- Chốt Git commit/tag sau review của người phụ trách; hiện còn thay đổi chưa commit.

Không đánh dấu toàn bộ tuần 7 đã nghiệm thu: phần backend độc lập có bằng chứng,
nhưng FE, ML và môi trường production vẫn cần phối hợp thực tế.
