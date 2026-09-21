# 4. Kiểm thử và bàn giao

## Test tự động

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_scans.py
.\.venv\Scripts\python.exe -m mypy app scripts
.\.venv\Scripts\python.exe -m compileall -q app scripts tests
```

Pytest dùng database riêng có tên kết thúc `_test`, tạo/xóa trong lúc chạy. Không
trỏ `TEST_DATABASE_URL` vào database có dữ liệu thật.

## Test ảnh thật

13 ảnh đã kiểm checksum trong `docs/predict-selection-audit/images/` gồm 10 ảnh
lá và 3 ảnh không phải lá. Lệnh sau chạy 78 request (ensemble và single model)
trên DB test và tạo report JSON mới:

```powershell
$env:PREDICT_SAMPLE_AUDIT='my-real-audit.json'
$env:PREDICT_SAMPLE_SINGLE='1'
.\.venv\Scripts\python.exe -m pytest -q tests/test_predict_downloaded_samples.py
Remove-Item Env:PREDICT_SAMPLE_AUDIT
Remove-Item Env:PREDICT_SAMPLE_SINGLE
```

Lần kiểm thử gần nhất: 78/78 request HTTP thành công. Report:
[real-audit-20260919.json](../predict-selection-audit/real-audit-20260919.json).

## Giới hạn bắt buộc phải truyền đạt

Predict và Grad-CAM đã hoạt động, nhưng backend chưa có detector lá/chất lượng ảnh
được nghiệm thu. `is_valid_leaf` chỉ là cờ policy accepted cũ; Grad-CAM chỉ minh
họa vùng model chú ý. Không được diễn đạt chúng là bằng chứng chẩn đoán.
