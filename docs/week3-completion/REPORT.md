# Hoàn thiện backend tuần 3

Ngày thực hiện: 07/09/2026. Phạm vi là tích hợp ba classifier, Predict, lưu kết quả và khả năng kiểm chứng backend. Không sửa frontend, không thêm workflow quản trị model hoặc Grad-CAM của các tuần sau.

## 1 Kết luận

Backend tuần 3 đã được bổ sung và kiểm thử bằng cả trọng số thật và PostgreSQL riêng. Không cần thêm file hoặc câu trả lời từ người làm ML để chạy pipeline hiện tại. Tuy nhiên, ngưỡng confidence 0.3 **không phải bộ nhận diện ảnh không phải lá**. Kiểm thử thực tế với ảnh tổng hợp đã chứng minh hạn chế này; không ghi nhận OOD là đã được nghiệm thu.

PostgreSQL chính tại 127.0.0.1:55432 chưa kết nối được và Docker engine không hoạt động trong phiên này. Vì thế migration mới **chưa áp dụng vào database chính**. Kiểm thử dùng cluster PostgreSQL 18 tạm ở localhost:55439, database có hậu tố `_test`, không thay đổi `.env` hoặc dữ liệu hiện tại.

## 2 Các thay đổi và tác dụng

| Phần | Thực hiện | Tác dụng và tương thích |
| --- | --- | --- |
| Preprocessing | RGB, resize 224×224 với bilinear và antialias tường minh; không crop, không tự xoay EXIF; ToTensor và ImageNet normalization | Khóa hành vi eval đang có; test ảnh không vuông đối chiếu pipeline ML local bằng tensor bằng nhau |
| Artifact | Chặn path thoát bundle; temperature phải là số hữu hạn dương; kiểm task, class order, checksum và metadata | Không nạp nhầm checkpoint/metadata hoặc chấp nhận NaN/Inf |
| Inference | Chặn logits sai shape, không hữu hạn; kiểm model specs đúng mode | Lỗi model trở thành lỗi/degraded có kiểm soát, không ghi kết quả số hỏng |
| Policy | Chụp cấu hình một lần trước chạy; giữ confidence 0.3, margin 0.05, JS 0.3 | Kết quả và audit không lệch nhau nếu cấu hình thay đổi trong lúc xử lý |
| Lịch sử | Thêm `scans.inference_snapshot` JSONB nullable và field response cùng tên | Lưu preprocessing, threshold, model ID/version/hash/temperature, model thất bại và weight thực tế; record cũ giữ null |
| Ảnh | Thêm GET `/api/v1/scans/{scan_id}/image` | Chủ Scan xem ảnh qua Bearer; Admin không bypass; kiểm traversal, không public uploads; private/no-store và nosniff |
| Upload | Giải mã pixel sau khi kiểm giới hạn kích thước | JPEG bị cắt dữ liệu nhận 422 trước inference thay vì lỗi model 503; giữ JPEG/PNG và giới hạn hiện có |
| Persistence | Validate response trước ghi file; commit Scan và kết quả con cùng transaction; bỏ refresh sau commit | Tránh đã commit Scan rồi refresh lỗi khiến xóa nhầm ảnh của record đã lưu |
| Phiên và Farm | Nhả read transaction khi inference; trước lưu kiểm lại token_version/role dưới lock User; kiểm creator khớp owner khi gán Farm | Logout hoặc đổi role trong lúc xử lý không tạo Scan mới; giữ best-effort Farm cho người đăng nhập |
| Tài nguyên | LRU cache tối đa 6 model; hai luồng PyTorch mặc định; giữ semaphore và timeout hiện có | Hạn chế RAM khi có nhiều version và tránh ba model đều chiếm toàn bộ CPU; model đang dùng vẫn có reference riêng |
| Tự kiểm chứng | `scripts.verify_week3` và các regression test | Có thể tự kiểm artifact, số hữu hạn, ba mode và parity mà không cần người làm ML chạy hộ |

Không đổi thành phần mode: Guest Basic dùng EfficientNet; User/Manager tối đa Standard dùng EfficientNet + MobileNet; Technician/Admin tối đa Advanced dùng cả ba. Advanced cần ít nhất hai model thành công; Standard có thể degraded còn một. Snapshot ghi weight bằng nhau giữa những model thành công, model lỗi có weight 0.

## 3 Migration và API

Migration mới `a7b8c9d0e1f2` nối sau `f6a7b8c9d0e1`. Chỉ thêm một cột nullable, không tạo lại database, không backfill cấu hình lịch sử và không thay số bảng nghiệp vụ (vẫn 8).

| API | Thay đổi |
| --- | --- |
| POST `/api/v1/predict` | Thêm `inference_snapshot`; giữ các field và mã lỗi hiện có, thêm kiểm tra phiên trước persistence |
| GET `/api/v1/scans/{scan_id}` | Thêm `inference_snapshot`; legacy có thể null |
| GET `/api/v1/scans/{scan_id}/image` | API mới; 200 ảnh, 401 chưa đăng nhập, 403 khác chủ, 404 thiếu Scan/file hoặc path không hợp lệ |
| GET `/api/v1/predict/capabilities` | Không đổi contract mode |

Danh mục nghiệp vụ nay có 28 endpoint do bổ sung API ảnh. Bộ Word ngày 07/09 là đánh giá trước thay đổi này; báo cáo này cập nhật trạng thái riêng của tuần 3. Các đề xuất tuần 1–2/4–8 trong bộ Word chưa mặc nhiên được triển khai.

## 4 Kiểm thử đã thực hiện

- Bộ test đầy đủ ở vòng kiểm tra cuối: **112 passed**, 32.74 giây, 2 cảnh báo dependency.
- Có kiểm thử API với **ba checkpoint thật**: Guest không lưu; User/Standard lưu hai model results; Admin/Advanced lưu ba; đọc ảnh và snapshot đúng quyền.
- Migration chạy từ rỗng qua revision cũ, tạo Scan legacy, upgrade head, xác minh record được giữ và snapshot null, rồi downgrade trên database test riêng.
- Mypy: không lỗi trong 73 file gồm app, tests và script xác minh. Compileall: đạt.
- Hai cảnh báo dependency hiện có: Starlette/httpx và passlib/argon2; chưa thay thư viện ngoài phạm vi tuần 3.

### Kết quả model thật

File `real-model-verification.json` ghi 24 lượt: 4 ảnh tổng hợp × 3 mode × 2 cách chạy. Tất cả lượt đều chạy đủ model, trả số hữu hạn, Top-3 hợp lệ; confidence và candidate khớp giữa chạy tuần tự/song song (sai số cho phép 1e-5).

Môi trường đo: CPU, Python 3.12.0, torch 2.13.0+cpu, torchvision 0.28.0+cpu, 2 luồng PyTorch. Đây là smoke test có cả cold load, không phải báo cáo p95 dưới tải.

**14/24 lượt được policy chấp nhận**, tương ứng 7/12 cặp ảnh–mode lặp lại theo hai cách chạy, không phải 24 ảnh độc lập. Ví dụ ảnh trắng có confidence khoảng 0.444 ở Basic, 0.552 ở Standard và 0.379 ở Advanced. Ảnh nhiễu được Basic chấp nhận nhưng Advanced từ chối trong probe này.

Do đó:

- Giữ `0.3` là baseline từ chối confidence; không tự tăng ngưỡng chỉ để làm xanh bốn ảnh tổng hợp.
- `is_valid_leaf` là field tương thích biểu thị policy accepted; không phải kết luận phát hiện lá.
- `ood_score` là heuristic, snapshot ghi `ood_detector_validated=false`.
- Không tính accuracy, macro-F1 hoặc tỷ lệ OOD đại diện từ bốn ảnh tổng hợp. Model classification vận hành được không đồng nghĩa chất lượng ảnh ngoài miền đã bảo đảm.
- Khi sử dụng thật, chỉ trình bày kết quả là tham khảo trong các nhãn hỗ trợ. Nếu yêu cầu bắt buộc từ chối ảnh không phải lá, đó vẫn là tiêu chí chất lượng chưa đạt, dù backend chạy và test kỹ thuật đạt. Có thể tự xây bộ ID/OOD độc lập để đánh giá tiếp; không bắt buộc chờ người làm ML cung cấp.

## 5 Hướng dẫn chạy và test

Chạy PowerShell tại `C:\Project\plant-disease\backend` sau khi PostgreSQL cấu hình trong `.env` hoạt động:

```powershell
.\.venv\Scripts\python.exe -m scripts.check_database
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Không chạy code mới ghi Scan trước khi migration thêm cột snapshot. Nếu database đã có model versions đúng checksum thì không cần seed lại. Chỉ khi dựng database mới và đã đặt đủ model bundles mới chạy `python -m scripts.seed_week2`; lưu ý tài khoản demo không dùng production.

### Kiểm tra bằng Swagger

1. Mở `/docs`, GET capabilities khi chưa đăng nhập: chỉ Basic.
2. POST predict với ảnh JPEG/PNG, không farm_id: HTTP 200 và scan_id null; xem validation_status và inference_snapshot.
3. Login User, bấm Authorize bằng access token, POST predict mode auto: Standard, hai model_results, có scan_id. Gửi Advanced bằng User phải nhận 403.
4. GET scans/{id}: snapshot phải giống response lúc predict. GET scans/{id}/image: ảnh trả về đúng. Admin hoặc user khác gọi API ảnh này phải nhận 403.
5. Technician/Admin predict auto: Advanced, ba model_results khi cả ba bundle khỏe mạnh.
6. File không phải ảnh nhận 415/422; JPEG cắt dữ liệu nhận 422; ảnh vượt giới hạn nhận 413. Guest gửi farm_id nhận 400.
7. Xóa Scan bằng chủ sở hữu: 204; detail/ảnh sau đó 404; kết quả con và file được dọn.

### Chạy tự động

```powershell
# Database test được tạo/xóa tự động; tuyệt đối không trỏ TEST_DATABASE_URL tới dữ liệu cần giữ.
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m mypy app tests scripts/verify_week3.py
.\.venv\Scripts\python.exe -m scripts.verify_week3 --output ../docs/week3-completion/real-model-verification.json
```

Hai biến mới tùy chọn trong `.env` là `MAX_CACHED_MODELS=6` và `TORCH_NUM_THREADS=2`. Không cần thêm thủ công nếu dùng giá trị mặc định. Điều chỉnh theo RAM/CPU thực, số worker và benchmark; không coi số đo smoke test là cam kết tải production.
