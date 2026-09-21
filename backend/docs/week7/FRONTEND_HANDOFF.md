# Hợp đồng tích hợp backend — 1.1.0-rc.2

Ngày: 16/09/2026. Chỉ bàn giao contract và kịch bản; chưa sửa/build frontend.
Nguồn máy đọc: [openapi.json](openapi.json). Không lấy danh sách API trong ba
Word cũ làm hiện trạng. Có 41 thao tác nghiệp vụ dưới `/api/v1`; `/`,
`/health/live`, `/health/ready` là endpoint vận hành ngoài số này.

[fixtures.json](fixtures.json) có ví dụ User, trang Farm/rỗng, Disease, Proposal,
Stats và lỗi; được kiểm tra khớp response schema. Dùng dựng giao diện/mock, không
import làm dữ liệu thật, không chứa tài khoản/token hoặc kết quả ML thực.

## 1. Kiểm soát thay đổi contract

```powershell
# Trong backend, cấu hình môi trường hợp lệ; không cần kết nối DB/model để export.
.\.venv\Scripts\python.exe -m scripts.export_contract --check
# Chỉ sau khi đã rà soát/thông báo thay đổi cho FE:
.\.venv\Scripts\python.exe -m scripts.export_contract
```

Test so sánh toàn bộ OpenAPI với snapshot. Thay đổi path, schema hoặc mã lỗi
phải review lại và xuất snapshot mới, không chỉ sửa tài liệu thủ công.
`1.1.0-rc.2` là định danh ứng viên API, chưa phải bản production hoặc Git tag.

## 2. Auth, cookie và role

- Login nhận JSON username/password, trả access_token. Access gửi qua header
  `Authorization: Bearer <token>`; không đặt token trong query URL ảnh.
- Refresh nằm trong HttpOnly Cookie; FE không đọc cookie bằng JavaScript.
  Login/refresh/logout cần `credentials: "include"` khi gọi khác origin.
- CORS mặc định cho localhost:5173 và 127.0.0.1:5173. Môi trường thật phải cấu
  hình origin chính xác, HTTPS và cookie phù hợp; không dùng wildcard credentials.
- Bổ sung tuần 8: các request Auth ghi dữ liệu/cookie có Origin phải thuộc
  CORS_ORIGINS hoặc PUBLIC_API_ORIGIN, nếu không trả 403 trước xử lý nghiệp vụ.
  Browser tự gửi Origin; FE không cần thêm custom header. Swagger cần đúng
  PUBLIC_API_ORIGIN (ví dụ dùng localhost:8000 thay vì 127.0.0.1:8000 thì sửa cấu hình).
  Response Auth đặt Cache-Control: no-store. Path và JSON schema không đổi.
- Bổ sung rc.2: các POST login/register/refresh/change-password có quota riêng
  theo IP client (IPv6 /64), dùng chung qua PostgreSQL. HTTP 429 kèm Retry-After
  (giây): hiển thị chờ, không lập vòng lặp refresh/retry. Logout không bị quota
  Auth này chặn. Proxy phải được cấu hình tin cậy; không tự gửi X-Forwarded-For.
- Response có X-Request-ID do server sinh, FE có thể đính kèm mã khi báo lỗi.
  CORS expose X-Request-ID/Retry-After, không cần custom request header mới.
- Nếu access hết hạn, có thể refresh rồi retry một lần. Nếu refresh thất bại,
  quay về đăng nhập, không lặp refresh vô hạn.
- Đổi mật khẩu/logout/đổi status thu hồi mọi token cũ. Mở khóa không khôi phục
  phiên cũ. Phân quyền dùng role/trạng thái trong DB, không tin role FE tự gán.
- Guest không là role DB; Managed User vẫn là role user có created_by.

| Nhóm | Được dùng | Không được suy diễn |
| --- | --- | --- |
| Guest | Register/login, tra cứu bệnh, Predict Basic | Không có lịch sử lưu trữ hoặc Farm |
| User | Scan riêng; Farm được giao nếu là Managed User | Không có Farm CRUD hoặc xem Scan thành viên khác |
| Manager | Farm sở hữu, Managed User do mình tạo, thành viên, thống kê Farm | Không xem Scan cá nhân của User qua API owner-only |
| Technician | Đề xuất sửa nội dung, xem đề xuất mình gửi | Không xuất bản trực tiếp hoặc duyệt đề xuất |
| Admin | Tài khoản, nội dung, duyệt, thống kê và giám sát riêng | Không kế thừa Farm CRUD hoặc bypass Scan owner-only |

## 3. Hợp đồng danh sách và lỗi

Các API danh sách phân trang trả **array**, không phải `{items,total}`.
`limit` mặc định 50, tối đa 100; `offset>=0`. FE chủ động tăng offset nếu cần
thêm dữ liệu, không coi trang đầu là toàn bộ danh sách. Response không cung cấp
tổng bản ghi riêng; đến trang ngắn hơn limit thì dừng.

| HTTP | Ý nghĩa/hiển thị |
| --- | --- |
| 400 | Lỗi nghiệp vụ như mật khẩu hiện tại sai hoặc request Guest gắn Farm |
| 401 | Chưa đăng nhập, token hết hiệu lực, tài khoản bị khóa |
| 403 | Sai role, không sở hữu đối tượng hoặc Auth Origin không được phép |
| 404 | Không tìm thấy đối tượng/ảnh hoặc đối tượng đã bị ẩn |
| 409 | Trùng liên kết, revision cũ, quyết định duyệt đối nghịch, xung đột trạng thái |
| 413/415 | Ảnh quá lớn hoặc không đúng định dạng |
| 422 | Validation; field thiếu/null sai/ngoài schema/giá trị enum không hợp lệ |
| 429 | Vượt quota Auth; chờ số giây trong Retry-After, không retry liên tục |
| 500 | Lỗi server không xử lý được; thông báo chung và X-Request-ID để đối chiếu log |
| 503/504 | Chưa sẵn sàng/bận hoặc quá thời gian; không hiển thị như kết quả chẩn đoán |

`detail` có hai dạng hiện hành, contract không ép mọi lỗi thành chuỗi:

```json
{"detail":"Không có quyền"}
```

```json
{"detail":[{"type":"missing","loc":["body","username"],"msg":"Field required","input":{}}]}
```

Mã lỗi khai báo chung trong OpenAPI là tập khả năng; không có nghĩa mọi route
đều phát sinh mọi mã. `204` không có body, không gọi `.json()` trên response này.

## 4. Những field dễ tích hợp sai

- Farm/Disease update: không gửi field = giữ nguyên. `null` chỉ dùng xóa field
  tùy chọn như location_text/description/treatment. Không gửi name/disease_name/
  severity_level=null. owner_id, role, reviewer_id, label_key không phải field
  được phép đổi tùy ý.
- `/me/farms`: Manager nhận Farm sở hữu; Managed User nhận Farm được giao đúng
  Manager; User độc lập/Technician/Admin nhận []. Không thay thế `/farms` CRUD.
- Ảnh cá nhân: `/scans/{id}/image`. Admin giám sát: `/admin/scans/{id}/image`.
  Dùng fetch có Bearer rồi tạo blob URL; revoke blob URL khi không dùng nữa.
  `image_path` trong JSON là logical storage path, không phải URL public.
- Proposal là bản nội dung thay thế của nhãn có sẵn, không phải PATCH. Lấy
  content_version mới nhất rồi gửi base_content_version; lỗi 409 yêu cầu tải
  lại nội dung, không tự động gửi lại bản cũ. Reject bắt buộc review_note.
- Stats dùng from/to có timezone; khoảng `[from,to)`. Tỷ lệ rejection 0..1,
  FE nhân 100 khi hiển thị %. null là chưa có mẫu đủ điều kiện, không phải 0%.
  Legacy tách riêng. Inventory User/Farm ở overview không bị lọc theo from/to.
- Predict giữ contract hiện có: single bắt buộc model_type, ensemble không
  nhận model_type. FE lấy capabilities, không tự hardcode quyền model.
  accepted/is_valid_leaf không xác nhận ảnh là lá. Không dùng top-k của Scan
  bị từ chối như chẩn đoán hoặc tự hiển thị treatment.

## 5. Kịch bản nghiệm thu chung với FE (chưa thực hiện)

1. Guest tra cứu bệnh, mở Predict; kiểm tra lỗi file không hợp lệ, không có history.
2. User đăng ký/login/refresh; đọc history/ảnh riêng; thử URL ảnh người khác bị chặn.
3. Admin tạo Manager và Technician; Manager tạo 2 Managed User và 1 Farm, gán thành viên.
4. Managed User chọn Farm qua /me/farms; không truy cập Farm CRUD. Gỡ membership,
   tải lại UI và xác nhận Farm biến mất.
5. Kiểm tra stats và phân trang, bộ lọc giờ có timezone, danh sách rỗng.
6. Technician gửi đề xuất; Admin duyệt/từ chối; tạo xung đột revision và hiển thị 409.
7. Admin khóa User; UI xử lý token cũ 401; mở khóa bắt login lại.
8. Đổi mật khẩu/logout, đóng trang/mở lại; không bị vòng lặp refresh.

Backend có kịch bản API xuyên suốt ở test_week7_contract_e2e.py dùng JWT/DB thật,
nhưng inference giả lập. Nó không thay thế browser E2E, FE build, cookie trên
domain triển khai hay nghiệm thu ảnh/model thật.

## 6. Điều kiện trước khi tích hợp

- Backup DB, nâng schema tới `c9d0e1f2a3b4`, restart backend.
- `/health/live` chỉ xác nhận tiến trình phản hồi.
- `/health/ready` chỉ kiểm DB và đúng migration; **không** xác nhận model sẵn sàng.
- Dùng `/docs` hoặc OpenAPI snapshot cùng phiên bản. Chốt môi trường URL/origin
  với người phụ trách BE trước kiểm thử trình duyệt.
