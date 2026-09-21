# Rà soát Predict, thử ảnh tải từ Internet và chọn model

Ngày: 08/09/2026. Chỉ sửa `backend/`; không sửa `ml/`, frontend, trọng số hoặc
temperature đã bàn giao. Giữ toàn bộ thay đổi tuần 3 đang có trước lượt này.

## 1. Kết luận chính

Basic/Standard/Advanced khác nhau về tập model nên có thể khác nhãn và quyết định
accepted/rejected. Không thể coi việc Basic true, Standard false, Advanced true
là lỗi boolean nếu chưa xem confidence/margin/JS. Một test kiểm soát xác suất đã
tái hiện chính xác chuỗi true/false/true theo toán học của ensemble. Không sửa
policy thành “có một model true thì tất cả true”, không tự nâng/hạ threshold.

Đã bổ sung chạy riêng model theo quyền, decision_details giải thích từng điều
kiện, lưu lựa chọn và quyết định vào Scan. Kết quả ensemble cũ trên 13 ảnh không
thay đổi sau bổ sung. **Không coi đây là bản sửa xong nhận diện ảnh không phải lá.**

## 2. Ảnh và phương pháp kiểm thử

Đã tải 13 file vào `backend/docs/predict-selection-audit/images/`:

- 10 ảnh lá, hai mẫu mỗi nhóm: Apple healthy, Apple scab, Tomato early blight,
  Tomato healthy, Grape black rot; từ thư mục test của PlantDoc.
- 3 ảnh không phải lá: astronaut, coffee, Chelsea cat; từ scikit-image 0.24.

Nguồn:

- [PlantDoc Dataset](https://github.com/pratikkayal/PlantDoc-Dataset), commit
  `5467f6012d78d1c446145d5f582da6096f852ae8`. Repository ghi CC BY 4.0;
  tác giả Davinder Singh, Naman Jain, Pranjali Jain, Pratik Kayal, Sudhakar Kumawat,
  Nipun Batra. Nhãn tham chiếu lấy từ thư mục, không được xác minh bệnh độc lập.
- [scikit-image sample data](https://scikit-image.org/docs/0.24.x/api/skimage.data.html),
  commit `a160f384523ac70173d069954b7084bee79fb68e`. Astronaut lấy từ NASA;
  coffee: Rachel Michetti, CC0; Chelsea cat: Stefan van der Walt, CC0.

`samples.json` lưu tên, URL download cố định, nguồn, label tham chiếu và SHA-256.
Không sửa/crop file nguồn đã tải. Ảnh không đưa vào Git; có script tải lại.

**Không phải benchmark accuracy/OOD độc lập:** chỉ có 13 ảnh chọn thuận tiện;
PlantDoc có thể đã được ML dùng khi train. Không có bằng chứng loại trùng với tập
train. Không dùng kết quả này để chọn lại ngưỡng hay khẳng định model nào tốt nhất.

### Cách thực thi

Trước sửa: 13 ảnh × 3 ensemble = **39 POST Predict**, lưu trong `before.json`.
Sau sửa: 13 ảnh × (3 ensemble + 3 single) = **78 POST Predict**, lưu `after.json`.
Tất cả trả 200, đủ số model yêu cầu. Mỗi request authenticated còn kiểm GET Scan
detail, persistence và không có điều trị khi policy từ chối.

Dùng FastAPI TestClient qua route/dependencies/schema/service thật, ba trọng số
thật và PostgreSQL test. Không mock inference trong test ảnh này. Session database
được trỏ sang DB test, upload dùng thư mục tạm; không tạo 117 Scan thử nghiệm trong
DB ứng dụng. Đây là kiểm thử ứng dụng HTTP/ASGI trong tiến trình, không phải đo
network/reverse proxy hay kiểm chứng Uvicorn production.

## 3. Kết quả mẫu

Số “đúng” dưới đây chỉ so label với nhãn thư mục PlantDoc. Phải đọc cùng số bị từ
chối; không diễn giải 6/6 là model có accuracy 100% trên mọi ảnh.

| Cách chạy | Ảnh lá accepted / 10 | Khớp nhãn trong ảnh lá accepted | Ảnh không lá accepted / 3 |
|---|---:|---:|---:|
| Basic ensemble (EfficientNet) | 10 | 8/10 | 2 |
| Standard ensemble (EfficientNet + MobileNet) | 7 | 6/7 | 0 |
| Advanced ensemble (cả ba) | 6 | 6/6 | 1 |
| Single EfficientNet | 10 | 8/10 | 2 |
| Single MobileNet | 10 | 7/10 | 2 |
| Single ResNet50 | 10 | 9/10 | 2 |

Điều đáng chú ý: Standard từ chối ba ảnh không phải lá trong nhóm này, nhưng cũng
từ chối ba ảnh lá. Single cho phép người dùng chọn đúng backbone nhưng không
phải cơ chế tăng độ an toàn; có thể mất tín hiệu bất đồng của ensemble.

### Ví dụ cụ thể: apple_healthy_2

| Mode | Confidence | Margin | JS | Quyết định |
|---|---:|---:|---:|---|
| Basic | 0.801323 | 0.700910 | 0 | accepted |
| Standard | 0.402369 | 0.053448 | 0.761892 | ambiguous: model_disagreement_too_high |
| Advanced | 0.373449 | 0.100495 | 0.604031 | ambiguous: model_disagreement_too_high |

Standard ở đây vượt confidence 0.3 và margin 0.05, nhưng JS vượt 0.3 nên bị từ
chối. Chỉ nhìn confidence sẽ không giải thích được kết quả.

### Ví dụ quan trọng: ảnh astronaut không phải lá

| Mode | Confidence | Margin | JS | Quyết định |
|---|---:|---:|---:|---|
| Basic | 0.350190 | 0.037710 | 0 | ambiguous: margin quá nhỏ |
| Standard | 0.434264 | 0.274332 | 0.328899 | ambiguous: bất đồng |
| Advanced | 0.580075 | 0.464857 | 0.240873 | accepted — false acceptance |

ResNet50 có confidence cao trên ảnh này, kéo phân bố tổng hợp thay đổi. JS hiện
còn chuẩn hóa theo log(số model thành công); điểm của hai và ba model không phải
cùng một tập phân bố đầu vào. Không có bảo đảm tính đơn điệu giữa các mode.

Trên 13 ảnh chưa gặp đúng chuỗi Basic true / Standard false / Advanced true của
người dùng. Tuy nhiên, test kiểm soát với EfficientNet/ResNet `[0.7,0.25,0.05]`
và MobileNet `[0.25,0.7,0.05]` tái hiện đúng chuỗi: hai model hòa top-1/top-2,
thêm model thứ ba làm margin tăng. Vẫn cần ảnh gốc/response của người dùng để
khẳng định nguyên nhân chính xác cho lần test đó.

So sánh 39 ensemble trước/sau: label, confidence, validation_status và
rejection_reason **không đổi**. Policy version đổi để đánh dấu hợp đồng mới;
không thay trọng số, temperature hay ngưỡng để ép true/false.

## 4. Những gì sửa trong code

### 4.1 Chọn riêng model

Multipart request bổ sung:

- `strategy=ensemble` mặc định: giữ hành vi mode cũ, không nhận model_type.
- `strategy=single`: bắt buộc model_type; chỉ truy vấn/load đúng active+enabled
  version của model được chọn. Không cần hai model còn lại active.
- `mode=auto` resolve tier theo role. Nếu chủ động chọn mode thấp hơn, model phải
  thuộc mode đó, kể cả người gọi là Admin.
- Không cho client gửi đường dẫn trọng số hoặc tự chọn version ID.

| Người gọi | Single model được phép khi mode=auto |
|---|---|
| Guest | efficientnet_b0 |
| User / Manager | efficientnet_b0, mobilenet_v2 |
| Technician / Admin | efficientnet_b0, mobilenet_v2, resnet50 |

Không mở thêm quyền Guest hoặc User. Admin không có quyền mới để cấu hình tier
trong lượt này; đó vẫn là nghiệp vụ quản trị khác.

Lỗi: thiếu model_type khi single hoặc gửi model_type khi ensemble = 422;
model/strategy ngoài enum = 422; vượt role/mode = 403; model được chọn không
active/enabled hoặc inference lỗi = 503. Không tự fallback sang backbone khác.
Advanced single chỉ cần một model, không bị coi là degraded; Advanced ensemble
vẫn giữ yêu cầu tối thiểu hai model thành công như trước.

### 4.2 Giải thích quyết định

Response thêm `inference_strategy`, `selected_model_type` và `decision_details`.
decision_details có:

- mỗi điều kiện: rule, value chưa làm tròn, threshold thực dùng, comparison,
  passed;
- failed_rules: mọi điều kiện không đạt, không chỉ lý do đầu tiên;
- aggregation, js_normalization và danh sách effective_model_types.

`rejection_reason` vẫn trả lý do ưu tiên đầu tiên, giữ tương thích. Confidence
hiển thị làm tròn sáu số có thể sát ngưỡng; xem raw value trong decision_details
khi cần giải thích. `model_results[].accepted` nay kiểm cả confidence lẫn margin
của model để nhất quán với chạy single, không còn chỉ kiểm confidence. Cờ per-model
không thể biểu diễn điều kiện bất đồng giữa nhiều model.

`is_valid_leaf` vẫn là cờ legacy policy; input_assessment tiếp tục thông báo chưa
có leaf detector. Không nên cho rằng accepted là xác nhận lá hoặc kết luận bệnh.

### 4.3 Lưu lựa chọn trong lịch sử

Thêm `scans.prediction_context JSONB NULL`: schema_version, inference_strategy,
selected_model_type và decision_details. GET Scan detail trả nguyên context đã
lưu; đổi threshold sau này không tính lại lịch sử. Model/version thực chạy vẫn
được lưu ở scan_model_results như trước.

Scan cũ có context null; không đoán single/ensemble từ dữ liệu thiếu. inference_mode
giữ basic/standard/advanced để tương thích, nhưng không dùng nó để suy ra số
model nữa; đọc strategy và models_requested/model_results.

## 5. Migration và dữ liệu ứng dụng

Phát hiện DB local ở a7b8c9d0e1f2 nhưng checkout thiếu file migration này. Đã khôi
phục migration inference_snapshot và khai báo cột tương ứng trong ORM để nối
đúng lịch sử, không stamp giả và không xóa cột đang có.

Chuỗi: `f6a7b8c9d0e1 → a7b8c9d0e1f2 → b8c9d0e1f2a3`.
Migration mới b8 chỉ thêm prediction_context nullable. DB local đã nâng từ a7
lên b8; **9 Scan trước và sau**, kiểm hash các giá trị cũ xác nhận không đổi.
`alembic check` không phát hiện lệch schema. Không seed lại, không đổi tài khoản,
mật khẩu hoặc cấu hình kết nối. Test migration còn kiểm dữ liệu legacy giữ null,
upgrade trên DB test và downgrade base chỉ trên DB test.

## 6. Hướng dẫn thử trên Swagger

Restart backend, mở `http://127.0.0.1:8000/docs`. Login và Authorize bằng access
token; nếu không đăng nhập thì chỉ có quyền Guest.

**Chạy riêng MobileNet bằng User hoặc Manager:**

```text
POST /api/v1/predict
file: chọn ảnh
mode: auto
strategy: single
model_type: mobilenet_v2
farm_id: bỏ trống nếu không gắn Farm
```

Kỳ vọng: inference_mode=standard, inference_strategy=single,
selected_model_type=mobilenet_v2, models_requested=1. Lịch sử có một model result
và prediction_context phản ánh lựa chọn.

**Chạy Standard ensemble:** mode=standard, strategy=ensemble, bỏ model_type.
Không gửi chuỗi rỗng cho field enum tùy chọn trong Swagger; bỏ tùy chọn gửi field
rỗng nếu UI bật nó. Kỳ vọng hai model được yêu cầu.

**Chạy riêng ResNet:** đăng nhập Technician/Admin, mode=auto hoặc advanced,
strategy=single, model_type=resnet50. User/Manager thử cùng request phải nhận 403.

**Chạy Basic cũ:** chỉ gửi file hoặc mode=basic, không gửi field mới; vẫn chạy
EfficientNet như trước. Request cũ không bị buộc thêm tham số.

## 7. Tự chạy lại test

Kết quả nghiệm chứng cuối: **112/112 test đạt** khi bật case ảnh thật, 86,38 giây;
mypy đạt trên 79 source file, compileall đạt. Có hai warning dependency
Starlette/httpx và argon2/passlib, không phải lỗi test. Thêm 20 regression case
cho lựa chọn model/quyền/decision_details ngoài case audit ảnh tải. Lượt cuối
chạy lại thêm 78 request ảnh thật, lưu local trong `final-verification.json`.
Hai báo cáo trước/sau dùng để so sánh chính thức là `before.json`, `after.json`.

Trong backend, dùng đúng môi trường `.venv`, PostgreSQL test có quyền tạo database:

```powershell
.\.venv\Scripts\python.exe -m scripts.download_predict_samples
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m mypy app tests scripts

# Bật test ảnh tải + trọng số thật; tên report phải chưa tồn tại.
$env:PREDICT_SAMPLE_AUDIT='my-verification.json'
$env:PREDICT_SAMPLE_SINGLE='1'
.\.venv\Scripts\python.exe -m pytest -q tests/test_predict_downloaded_samples.py
Remove-Item Env:PREDICT_SAMPLE_AUDIT
Remove-Item Env:PREDICT_SAMPLE_SINGLE
```

Test mặc định bỏ qua đúng một case ảnh tải vì phụ thuộc dữ liệu lớn/network setup;
test không tự tải ảnh ngầm. Khi bật, nó chạy cả 78 request. Các database *_test
được tạo/xóa bởi fixture: không chứa dữ liệu thật trong các DB này, không chạy
hai suite đồng thời trên cùng tên DB. Test uploads nằm ở thư mục tạm.

Khi triển khai máy khác, chạy `python -m alembic upgrade head` trước restart API.
Không downgrade trên DB có dữ liệu nếu không chấp nhận mất cột context/snapshot.

## 8. Giới hạn còn lại

Không có nhận diện lá hoặc OOD đã nghiệm thu; ba ảnh negative không đủ chọn policy
mới. Không ép Advanced chính xác hơn Standard, không tự chọn model theo kết quả
cao nhất trên từng ảnh. Người dùng chọn single có thể được accepted nhiều hơn
nhưng đồng thời tăng false acceptance. Cần tập ảnh độc lập đủ đa dạng để quyết
định thay threshold/JS hoặc bổ sung detector.

Không sửa frontend: FE cần tự bổ sung selector nếu muốn UI lựa chọn. API đã có
capabilities và OpenAPI để tích hợp. Không triển khai thanh toán, Grad-CAM, admin
model activation hoặc các task tuần sau trong lượt này.
