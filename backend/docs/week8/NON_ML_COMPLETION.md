# Bổ sung backend không ML sau mốc tuần 8 (rc.2)

Tài liệu này là phần bổ sung cho [báo cáo tuần 8 rc.1](REPORT.md), không thay
thế [quy trình triển khai](DEPLOYMENT.md). Code khai báo API `1.1.0-rc.2` và
schema `d0e1f2a3b4c5`. Revision mới thêm bảng `auth_rate_limits`; việc có file
migration trong repo **không có nghĩa** database ứng dụng đã được nâng cấp.

## Các thay đổi đã có trong code

| Phần | Hành vi |
| --- | --- |
| Auth rate limit | POST login/register/refresh/change-password dùng quota theo client và endpoint. Vượt quota trả 429 kèm `Retry-After`; lỗi DB limiter trả 503 thay vì bỏ qua bảo vệ. Logout vẫn gọi được khi chạm quota. |
| Nhận diện client | Dùng client host do ASGI cung cấp, không tin trực tiếp `X-Forwarded-For`. IP được băm HMAC trước khi lưu; IPv6 gom theo /64. |
| Đổi role qua CLI | `python -m scripts.update_role USERNAME ROLE --reason "..."` mặc định chỉ preview; thêm `--apply` mới ghi. Service kiểm tra bất biến Manager/Managed User/Admin cuối cùng, ghi audit và thu hồi token cũ khi đổi role. |
| Request log | Response có `X-Request-ID`; JSON access event ghi route đã định nghĩa, method, status, duration. Không ghi query string, body, credential hoặc đường dẫn lạ nguyên văn. |

Auth rate limit dùng bảng PostgreSQL chia sẻ giữa các worker, nên restart API
không reset quota. Đây không thay thế giới hạn request body, reverse proxy hay
bảo vệ trước tấn công phân tán. `X-Request-ID` là ID server sinh, không tin ID
client gửi. Browser được expose `X-Request-ID` và `Retry-After` qua CORS.

## Cách kiểm tra an toàn

Từ `backend`:

```powershell
python -m scripts.preflight
python -m alembic current
python -m alembic heads
```

`preflight` chỉ đọc. Nếu DB ứng dụng chưa ở `d0e1f2a3b4c5`, không bật các API
phụ thuộc bảng mới. Muốn nâng DB có dữ liệu, làm theo trình tự dừng writer,
backup/restore kiểm chứng và maintenance window trong [DEPLOYMENT.md](DEPLOYMENT.md);
không tự chạy migration chỉ vì tài liệu này được thêm.

Kiểm thử trên database **test** riêng sau khi xác nhận `TEST_DATABASE_URL` kết
thúc bằng `_test`:

```powershell
python -m pytest -q tests/test_non_ml_operations_hardening.py
python -m pytest -q
```

Fixture có thao tác tạo/xóa database `_test`, vì vậy không chạy hai suite đồng
thời trên cùng DB test. Các case chính nằm trong
[`tests/test_non_ml_operations_hardening.py`](../../tests/test_non_ml_operations_hardening.py).
Không dùng số test từ mốc rc.1 như bằng chứng rc.2 đã pass trên môi trường này.

## Giới hạn

Chưa kết luận database ứng dụng hiện đã migrate, API production đã triển khai,
frontend browser đã nghiệm thu, hoặc chất lượng ML/leaf detection/OOD đạt chỉ
từ việc code và test có mặt trong repo. [Báo cáo rc.1](REPORT.md) mô tả chi tiết
những giới hạn vận hành vẫn cần theo dõi.
