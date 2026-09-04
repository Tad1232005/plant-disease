# Hướng dẫn Backend Tuần 3 — Multi-model inference vertical slice

Tuần 3 nối upload ảnh với ba classifier, Disease Info, Farm authorization và
lịch sử Scan. Model được lazy-load ở request đầu tiên, nên Auth/CRUD vẫn khởi
động nếu chưa có lưu lượng inference.

## 1. Artifact contract

Mỗi version nằm trong một thư mục có `manifest.json`, `model.pt`, `classes.json`,
`model_type.json` và `temperature.json`. Seed kiểm tra đủ file, task
`disease_classification`, input 224×224, output logits, 38 class cùng thứ tự,
temperature dương và checksum SHA-256 trước khi đăng ký DB.

DB cho phép tối đa một version active trên **mỗi `model_type`**, không còn giới
hạn một model active trên toàn hệ thống. Ba type hiện hỗ trợ là
`efficientnet_b0`, `mobilenet_v2`, `resnet50`.

## 2. Request và quyền dùng mode

```http
POST /api/v1/predict
Content-Type: multipart/form-data
```

Form gồm `file` bắt buộc, `farm_id` tùy chọn và
`mode=auto|basic|standard|advanced` (mặc định `auto`).

| Actor | Auto mode | Model |
|---|---|---|
| Guest | Basic | EfficientNet-B0 |
| User/Manager | Standard | EfficientNet-B0 + MobileNetV2 |
| Technician/Admin | Advanced | cả ba model, thêm ResNet50 |

Client được chọn mode thấp hơn nhưng gửi mode cao hơn quyền sẽ nhận 403.
`GET /predict/capabilities` giúp FE dựng lựa chọn; server vẫn là nơi thực thi
quyền thật.

Backend giới hạn mặc định 10 MiB, 20 triệu pixel và 30 giây. Byte ảnh được đọc
bằng Pillow, không tin riêng MIME/tên file. Ảnh hỏng nhận 422, sai MIME 415, quá
lớn 413, timeout 504 và model/config lỗi 503 mà không lộ đường dẫn nội bộ.
`MAX_CONCURRENT_INFERENCES` giới hạn số lượt chẩn đoán chạy đồng thời
(mặc định 1). Slot chỉ được trả khi worker model thật sự dừng, kể cả
khi HTTP request đã timeout.

## 3. Ensemble và rejection baseline

Mỗi model trả logits. Backend áp dụng `softmax(logits / temperature)` rồi lấy
trung bình calibrated probabilities (soft-voting). Kết quả còn ghi:

- confidence ensemble và Top-3;
- margin Top1–Top2;
- normalized entropy;
- Jensen–Shannon divergence giữa model;
- energy score để thu thập dữ liệu, chưa dùng làm ngưỡng;
- agreement/degraded status, latency và lỗi riêng từng model.

Baseline từ chối nếu confidence `< 0,3`, margin `< 0,05` hoặc JS divergence
`> 0,3`. Khi từ chối, `label=null` và không trả nội dung điều trị. Tên field
`is_valid_leaf` được giữ để tương thích nhưng nghĩa chính xác là “policy chấp
nhận kết quả”, không phải leaf detector.

Temperature scaling chỉ hiệu chỉnh xác suất, **không phải OOD detection**. Các
ngưỡng trên phải được thay bằng kết quả đo từ tập ID/OOD thật (AUROC, FPR95 và
precision/recall tại operating point) trước khi tuyên bố dùng production.

## 4. Persistence và Farm

Guest không ghi file/DB. Với tài khoản đăng nhập, một workflow sẽ:

1. xác minh quyền gắn Farm (Manager sở hữu hoặc Managed User là member);
2. lưu ảnh atomically bằng UUID;
3. trong một transaction ghi `scans`, Top-3 ensemble và `scan_model_results`;
4. rollback và xóa file vừa lưu nếu DB lỗi.

Farm không hợp lệ không làm mất dự đoán: Scan vẫn được lưu với `farm_id=null`,
response có `farm_assignment_status="not_allowed"` và warning. Token Bearer sai
nhận 401, không bị coi như Guest.

## 5. Fail-soft

Basic/Standard cần ít nhất một model thành công; Advanced cần ít nhất hai. Nếu
vẫn đủ số model, response có `agreement_status="degraded"` và lưu lỗi riêng của
model hỏng. Nếu không đủ, toàn request nhận 503. Đây là khả năng chịu lỗi, không
có nghĩa kết quả degraded có chất lượng ngang ensemble đầy đủ.

## 6. Test

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_predict.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_ensemble.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_farm_members.py -q
```
