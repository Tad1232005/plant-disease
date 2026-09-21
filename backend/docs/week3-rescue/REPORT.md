# Hiệu chỉnh backend tuần 3 — 08/09/2026

## Phạm vi và điểm xuất phát

Chỉ sửa trong `backend/`. Không sửa `ml/`, frontend, trọng số hoặc metadata bundle.
Không đổi ngưỡng confidence 0.3, không train lại và không migrate database ứng dụng.

Checkout khi bắt đầu: nhánh `ngdinthie32`, commit `8f59ed1`, worktree sạch. Code
thực tế không giống trạng thái từng mô tả trong cuộc trò chuyện: vẫn dùng
Resize(256)/CenterCrop(224), chưa có một số hardening/snapshot trước đây. Lượt này
sửa trực tiếp code đang có, không tự khôi phục tất cả thay đổi của tuần 1/2/4.
Số lượng test của checkout này vì vậy không được đánh đồng với con số 144 đã báo
ở phiên trước.

## Những gì đã sửa và tác dụng

| Phần | Cách thực hiện | Tác dụng/ảnh hưởng |
|---|---|---|
| Preprocessing | RGB, resize 224×224 bilinear/antialias, không crop, ImageNet normalize | Khớp evaluation ML đã bàn giao; kết quả có thể khác pipeline crop cũ |
| Policy version | `ensemble-rgb224-v2` | Scan mới phân biệt được với kết quả pipeline cũ; không viết lại lịch sử |
| Ý nghĩa kết quả | InputAssessment trong Predict/capabilities; deprecated is_valid_leaf | Không gọi policy acceptance là bằng chứng nhận diện lá |
| Rejection | validation_status là nguồn quyết định; ép label null và legacy flag false khi không accepted | Không lộ kết luận/điều trị do cờ boolean không nhất quán |
| Accepted | Có warning kết quả tham khảo, chưa xác minh lá/loài hỗ trợ | Client hiện warning có thể hiển thị thêm; không đổi schema field warning |
| Scan detail | Chỉ tra điều trị khi validation_status accepted và legacy flag hợp lệ | Một chỉnh sửa liên quan tuần 4 để không đưa lại điều trị khi đọc Scan đã bị từ chối |
| Upload | Decode toàn bộ pixel sau kiểm byte/MIME/pixel limit | JPEG cắt đuôi bị trả 422 trước inference, không lỗi model 503 |
| Model output | Kiểm shape [1,C], NaN/Inf; temperature hữu hạn/dương | Output hỏng trở thành model failure, không được kết luận bệnh |
| Artifact | Chặn file vượt thư mục bundle, class duy nhất và ít nhất 2 lớp khi load | Tránh contract không hợp lệ và đường dẫn vượt phạm vi bundle |
| Cache | Key gồm toàn bộ ActiveModelSpec, LRU tối đa 6 model | Đổi metadata không dùng nhầm cache; giới hạn số model được giữ trong cache |
| Persistence | Validate response trước save; lấy scan_id trước commit, không refresh sau commit | Không ghi output phi hữu hạn; tránh dọn ảnh sau lỗi refresh dù DB đã commit |
| Config | Confidence/margin/JS phải hữu hạn, thuộc [0,1] | Cấu hình ngưỡng lỗi bị từ chối lúc khởi tạo |

Giới hạn cache là số entry, không phải quota RAM tuyệt đối. Model đang được request
sử dụng còn có thể ở bộ nhớ sau eviction; mỗi worker vẫn có cache riêng.

## Hợp đồng API và tương thích

Không thêm endpoint, không thay role/mode, không sửa enum database. Vẫn dùng
`accepted`, `low_confidence`, `ambiguous`, `model_error`. File hỏng dùng HTTP
413/415/422 hiện có, không lưu thành Scan. Model không đủ khả dụng vẫn dùng lỗi
503; timeout 504. Model lỗi một phần có thể chạy degraded theo policy cũ.

Predict/capabilities có thêm:

```json
{
  "input_assessment": {
    "leaf_detection_status": "not_performed",
    "quality_status": "not_assessed",
    "scope": "Ảnh cận cảnh một lá, đủ sáng và rõ nét; chỉ hỗ trợ các nhãn đã học.",
    "limitations": "Policy đạt không xác nhận ảnh là lá hoặc chẩn đoán chắc chắn đúng."
  }
}
```

Không đặt field `not_leaf` hoặc `poor_quality` giả định. Chưa có dữ liệu để nghiệm
thu bộ nhận diện lá hoặc ngưỡng chất lượng ảnh mờ/tối. Kiểm file decode được không
đồng nghĩa ảnh rõ nét hoặc là lá. Top-k/per-model labels vẫn tồn tại để audit;
client chỉ nên dùng label kết luận khi validation_status accepted.

FE chưa được chỉnh sửa. Field bổ sung không yêu cầu đổi client đọc JSON thông
thường, nhưng client strict schema cần chấp nhận field mới. Frontend tự diễn đạt
is_valid_leaf là “chắc chắn là lá” sẽ chưa được sửa chỉ bằng backend; đã ghi rõ
ngữ nghĩa mới trong OpenAPI và warning để người phụ trách FE có thể tiếp nhận.

## Công cụ kiểm thử ảnh thực tế

`scripts/evaluate_input_policy.py` chỉ đọc bundle và ảnh, không dùng DB. Chạy đủ
basic/standard/advanced với calibrated inference hiện tại; không fit temperature,
không tối ưu ngưỡng. Báo cáo ghi checksum/version/temperature, preprocessing,
ngưỡng, device và kết quả từng ảnh. Không có nhóm dữ liệu tương ứng thì metric
trả null, không giả định độ chính xác 100%.

Tạo manifest JSON (đường dẫn ảnh tương đối với manifest):

```json
[
  {"path": "images/tomato.jpg", "group": "in_scope", "expected_label": "Tomato___healthy"},
  {"path": "images/chair.jpg", "group": "non_leaf"},
  {"path": "images/unsupported-species.jpg", "group": "unsupported_leaf"}
]
```

Đây là ví dụ cấu trúc, không phải dữ liệu đã cung cấp. Chỉ gắn in_scope khi có nhãn
kiểm chứng; script yêu cầu expected_label thuộc bundle. Gom ảnh đã được phép sử
dụng, tách tập dùng chọn ngưỡng và tập nghiệm thu; không dùng chung rồi báo accuracy.

Từ backend:

```powershell
.\.venv\Scripts\python.exe -m scripts.evaluate_input_policy --manifest docs/week3-rescue/my-images.json --output docs/week3-rescue/real-images-report.json
```

Output bắt buộc là file mới trong backend để không ghi đè báo cáo/bundle. Ảnh lỗi
hoặc mode không đủ model làm script dừng, không xuất báo cáo thành công một phần.
Script đi tuần tự qua ảnh, gọi ensemble theo cấu hình song song hiện tại; giới hạn
Torch 2 thread cho tiến trình kiểm thử này, không thay cấu hình server.

Các metric gồm false-accept trên non_leaf/unsupported_leaf, rejection trên
in_scope và accuracy trong các ảnh in_scope đã accepted. Phải đọc cả ba, không
chỉ nhìn accuracy trên tập được giữ lại. Đây không phải báo cáo AUROC/FPR95.

## Kiểm thử model thật đã thực hiện

`synthetic-audit.json`: CPU, ba ảnh màu trơn trắng/đen/xanh, mỗi ảnh chạy ba mode,
tổng 9 lượt. Cả ba kiến trúc chạy; **3/9 lượt accepted**, đều là ảnh trắng.
Mỗi mode cho qua 1/3 ảnh ở probe này. Không suy rộng tỷ lệ đó sang ảnh thực tế.
Không có ảnh in_scope nên accuracy và tỷ lệ từ chối lá đúng là null.

Kết quả chứng minh cần giữ cảnh báo giới hạn: dù đã sửa preprocessing, confidence
0.3 và ensemble vẫn không phải bộ nhận diện lá. Chưa có tập ảnh thực tế được gán
nhãn trong lượt này nên chưa tuyên bố nghiệm thu chất lượng OOD hay bệnh.

## Cách chạy kiểm thử và phần hoãn lại

Kết quả cuối: **91/91 test đạt**, gồm 12 test mới trong `test_week3_rescue.py`;
mypy đạt trên 76 source file, compileall đạt. Hai warning thư viện còn lại là
Starlette/httpx và argon2/passlib, không phải test thất bại. Bộ test PostgreSQL
bao phủ cả các luồng tuần 1/2/4 đang có để kiểm regression.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m mypy app tests scripts
.\.venv\Scripts\python.exe -m compileall -q app scripts tests
```

Pytest tạo/xóa database chuyên test `plant_disease_test` và
`plant_disease_migration_test`, không phải database ứng dụng. Không đặt dữ liệu thật
vào các DB này; không chạy đồng thời hai suite cùng tên DB. Không cần migrate hoặc
seed lại DB ứng dụng cho các thay đổi lần này; restart backend để nạp code mới.

Tuần 1/2 không sửa. Tuần 4 chỉ có guard điều trị khi đọc Scan, là phụ thuộc của
tuần 3. Grad-CAM, dashboard, quản trị model, leaf/non-leaf training và nhận diện
chất lượng ảnh được để ngoài lần này. Rate limit phân tán và benchmark production
cũng chưa thực hiện; concurrency limit hiện có không thay thế chống spam Guest.
