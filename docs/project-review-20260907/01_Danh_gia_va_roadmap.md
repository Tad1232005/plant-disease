# Đánh giá dự án Plant Disease và kế hoạch 8 tuần

Bộ tài liệu 1 trong 3 • Ngày 07 tháng 09 năm 2026 • Phiên bản đề xuất 1

Dành cho người phụ trách Backend, Frontend, ML và người nghiệm thu đồ án.

## 1 Kết luận về tiến độ và tính khả thi

Backend đã triển khai phần lớn chức năng nền tảng của Tuần 1 đến Tuần 4. Dự án có thể hoàn thiện trong khung 8 tuần nếu ưu tiên luồng sử dụng đầy đủ và dành hai tuần cuối cho tích hợp, triển khai, sửa lỗi. Không nên quy đổi việc đã có backend bốn tuần thành dự án đã hoàn thành 50 phần trăm: chất lượng ML trên ảnh thực tế, giao diện tích hợp và khả năng vận hành cần nghiệm thu riêng.

Mốc kỹ thuật gần nhất trong phiên làm việc là 81 test backend đạt, mypy kiểm tra 71 file không lỗi và PostgreSQL ở migration head f6a7b8c9d0e1. Đây là kết quả kiểm tra của lượt sửa preprocessing trước đó, không phải chứng nhận mọi yêu cầu sản phẩm đã hoàn thành. Rà soát code hiện tại vẫn phát hiện các ca cập nhật null và các API hỗ trợ luồng dùng còn thiếu.

| Hạng mục | Hiện trạng | Cần làm trước nghiệm thu |
| --- | --- | --- |
| Auth và phân quyền | Register, login, refresh, me, logout và token_version | Đổi mật khẩu, khóa tài khoản, kiểm tra phiên bị thu hồi |
| PostgreSQL và schema | 8 bảng nghiệp vụ, Alembic, seed | Bỏ hướng dẫn SQLite cũ; kiểm tra backup và restore |
| Farm và nội dung bệnh | CRUD có giới hạn vai trò và sở hữu | Chặn null sai; bổ sung phân trang và kiểm soát field |
| Predict | 3 classifier, calibration, ensemble, lưu Scan | Kiểm chứng ensemble, threshold và ảnh thực tế |
| Managed User và Members | Luồng tạo và phân công đã có | API liệt kê Farm được giao cho màn chọn Farm |
| Lịch sử Scan | Owner-only, chi tiết, xóa | API lấy ảnh có quyền, xử lý vòng đời file |
| Quản trị và thống kê | Chưa có nhóm API hoàn chỉnh | Farm stats, Admin scans, tổng quan và khóa tài khoản |
| Giải thích và đề xuất bệnh | Chưa triển khai backend | Workflow tối giản, Grad-CAM theo model cụ thể |
| Frontend và triển khai | Do thành viên khác phụ trách | Nghiệm thu chung bằng kịch bản thực tế |

Ba tài liệu có vai trò khác nhau: tài liệu này quản lý tiến độ và rủi ro; tài liệu 2 quy định chức năng, role và API; tài liệu 3 quy định database, enum, CRUD và migration. Nhãn HIỆN CÓ chỉ chức năng đã thấy trong code. Nhãn ĐỀ XUẤT chỉ thay đổi phải triển khai và kiểm thử sau khi nhóm chốt phạm vi.

[PAGE]
## 2 Phạm vi sản phẩm nên giữ

Sản phẩm hỗ trợ người dùng gửi ảnh để tham khảo kết quả phân loại trong 38 nhãn, lưu lịch sử cá nhân, tra cứu nội dung bệnh và tổ chức hoạt động theo Farm. Manager quản lý Farm và người dùng do mình tạo. Technician đóng góp chuyên môn qua đề xuất nội dung. Admin kiểm soát tài khoản, nội dung và vận hành hệ thống bằng API riêng.

### Các quyết định thiết kế đề xuất

| Mã | Quyết định | Lý do và ảnh hưởng |
| --- | --- | --- |
| D01 | PostgreSQL là database duy nhất của bản triển khai | Alembic là nguồn quản lý schema; pgAdmin dùng quan sát và vận hành |
| D02 | Giữ 4 role, không thêm role Guest hoặc Managed User | Guest chưa đăng nhập; Managed User vẫn là user có người tạo là Manager |
| D03 | Quyền xét theo role và đối tượng | Admin không kế thừa Farm CRUD hoặc quyền xem Scan cá nhân của người khác |
| D04 | Giữ hợp đồng 27 API hiện tại trong giai đoạn tích hợp | Các thay đổi mã lỗi hoặc response phải có phiên bản và test phối hợp FE |
| D05 | 3 model cùng được đăng ký nhưng chỉ chạy nhóm model được mode chọn | Basic 1, Standard 2, Advanced 3 là cấu hình hiện tại, chưa chứng minh mode cao chính xác hơn |
| D06 | 0.3 là baseline confidence rejection | Chỉ công bố OOD sau khi có định nghĩa score và đánh giá riêng |
| D07 | Dashboard Farm trước Grad-CAM nâng cao | Luồng vận hành Manager có ích và dễ nghiệm thu trước tính năng chuyên sâu |
| D08 | Khóa User và archive Farm hoặc Disease | Tránh mất Scan và quan hệ lịch sử do xóa dây chuyền |

### Phân mức ưu tiên trong thời hạn

P0 là điều kiện để demo và triển khai: Auth, ảnh đầu vào hợp lệ, Predict với phản hồi trung thực, history và ảnh có quyền, Farm và members, thống kê cơ bản, PostgreSQL, test và backup restore. Các lỗi P0 chặn phát hành.

P1 là nghiệp vụ hoàn thiện: duyệt đề xuất sửa nội dung, Grad-CAM tối giản trên Scan của chính Technician hoặc Manager, đăng ký và activate phiên bản thuộc ba kiến trúc đã hỗ trợ. Có thể cắt Grad-CAM trước nếu chưa đạt luồng cốt lõi vào cuối Tuần 6.

P2 là mở rộng: Admin thay đổi thành phần Basic Standard Advanced qua database, thêm kiến trúc thứ tư, thanh toán thật, tự động retraining nhãn mới và dashboard thời gian thực. Việc Admin sửa mode đã được đề xuất trước đây nhưng code hiện chưa hỗ trợ; tài liệu 2 và 3 ghi riêng API và hai bảng cần thêm nếu giữ yêu cầu đó trong bản 8 tuần.

[PAGE]
## 3 Hiệu chỉnh Tuần 1 đến Tuần 4

Không làm lại nền tảng đã chạy. Dành đầu Tuần 5 cho những khoảng trống ảnh hưởng trực tiếp đến tính đúng đắn và luồng dùng.

| Tuần | Nền tảng giữ lại | Hiệu chỉnh cần thực hiện |
| --- | --- | --- |
| 1 | JWT 15 phút, refresh cookie 7 ngày, token_version, RBAC | Thêm users.status; đổi mật khẩu yêu cầu mật khẩu cũ; khóa tài khoản tăng token_version và kiểm tra status ở login, refresh, access |
| 2 | PostgreSQL, constraints, seed 38 bệnh và 3 model; Farm Manager-only | Chặn null cho name, disease_name và severity_level; whitelist field; kiểm tra label và bổ sung phân trang |
| 3 | RGB, resize 224×224 không crop, calibration riêng, soft voting | Ghi snapshot policy; thêm API đọc ảnh; kiểm chứng real-world, ensemble, rejection; FE dùng validation_status |
| 4 | created_by, unique membership, Scan owner-only | GET /me/farms; test thay đổi membership; không tự cấp quyền đọc Scan của thành viên cho Manager |

### Các lỗi và thiếu sót đã xác định

FarmUpdate và DiseaseInfoUpdate cho phép gửi null tới những cột database bắt buộc có giá trị. CRUD hiện gán các giá trị đó khi field xuất hiện trong request. Cần trả 422 ngay ở validation; vẫn cho phép null để xóa location_text, description hoặc treatment. Bộ test xanh trước đây chưa bao phủ các ca này.

Scan detail trả image_path nhưng chưa có đường HTTP đọc ảnh với kiểm tra quyền. Cần GET /scans/{scan_id}/image để người sở hữu xem lại ảnh. Không được suy ra image_path là một URL công khai đã hoạt động.

Managed User được gửi farm_id khi Predict nhưng không có API lấy danh sách Farm mình được giao. GET /me/farms khép kín luồng chọn Farm mà không mở Farm CRUD cho User.

Phân tầng mode hiện hardcode trong predict_service.py. Bảng model_versions chỉ giải quyết phiên bản active của từng kiến trúc. Thay thành phần một mode là một bài toán cấu hình riêng, cần policy có version nếu muốn Admin tự quản lý.

### Những hành vi cần mô tả đúng

Logout hiện thu hồi mọi thiết bị của tài khoản. Refresh tạo cookie mới nhưng token cũ chưa bị theo dõi reuse theo từng token family. Disease trong lịch sử được tra cứu bằng nội dung hiện hành; soft-delete giữ bản ghi nhưng không lưu lại nguyên văn treatment tại thời điểm dự đoán. Farm không hợp lệ hiện tạo Scan cá nhân kèm warning, không trả lỗi cho toàn bộ Predict. Các hành vi này phải hiển thị rõ trong tài liệu và FE.

[PAGE]
## 4 Kế hoạch Tuần 5 và Tuần 6

Tuần dưới đây là tuần chức năng trong roadmap, không phải khẳng định lịch làm việc thực tế đã trôi qua đúng bốn tuần. Người phụ trách nhóm cần đặt ngày lịch khi biết hạn nộp chính thức.

### Tuần 5 khép kín luồng vận hành

| Ngày | Backend | Phối hợp và tiêu chí đạt |
| --- | --- | --- |
| 1 | Sửa null update, whitelist, snapshot policy; triển khai staging tối thiểu | QA kiểm request thiếu field khác null; staging kết nối PostgreSQL và nhận model |
| 2 | GET /me/farms và GET /scans/{id}/image | FE chọn Farm được giao và xem ảnh history; người khác bị từ chối |
| 3 | Đổi mật khẩu, status User, thu hồi phiên, audit tối thiểu | Token cũ không dùng được sau đổi mật khẩu hoặc khóa; không khóa Admin cuối |
| 4 | Farm stats và Admin overview | Tổng số liệu khớp fixture; Farm chỉ aggregate Scan gắn đúng Farm |
| 5 | Admin scans, recent-invalid, ảnh giám sát; phân trang | Demo từ Manager tạo User đến Scan và dashboard; không bypass /scans owner-only |

Đầu ra ML cùng tuần: xác nhận preprocessing chi tiết, benchmark tổ hợp đang chạy và score 0.3. Báo cáo riêng ảnh thực tế để quyết định giữ hay đơn giản hóa Standard và Advanced. Chưa thay mode của backend chỉ dựa trên accuracy từng model.

### Tuần 6 hoàn thiện workflow có giới hạn

| Ngày | Backend | Điều kiện hoàn thành |
| --- | --- | --- |
| 1 | Migration disease_proposals, content_version, submit và mine | Technician gửi bản sửa nhãn hiện có; field được kiểm tra |
| 2 | Admin review, approve, reject trong một transaction | Hai lượt duyệt cạnh tranh chỉ một lượt thành công; xung đột revision trả 409 |
| 3 | Model registry list và register bundle đã được triển khai | Không nhận checkpoint hoặc URL tùy ý; kiểm tra manifest, checksum, class order |
| 4 | Activate theo model_type và rollback bằng version cũ | Warm-up trước đổi; một active mỗi type; lỗi không làm mất version đang chạy |
| 5 | Grad-CAM tối giản theo ScanModelResult nếu ML sẵn sàng | Chỉ Technician hoặc Manager là chủ Scan; dùng checkpoint lịch sử đúng version |

Ngày 5 là phần có thể cắt. Nếu Admin cấu hình mode là bắt buộc, dùng dung lượng P1 của Tuần 6 cho policy có version và dời Grad-CAM nâng cao ra sau nghiệm thu. Không cộng cả thanh toán, policy động và retraining vào cùng một ngày.

[PAGE]
## 5 Kế hoạch Tuần 7 và Tuần 8

### Tuần 7 tích hợp và đóng phạm vi

| Ngày | Công việc | Bằng chứng cần lưu |
| --- | --- | --- |
| 1 | Chốt OpenAPI, fixtures và luồng lỗi với FE | Phiên bản API dùng chung; FE build và smoke test |
| 2 | E2E Guest, User, Managed User, Manager, Technician, Admin | Kịch bản thành công và bị cấm; không chỉ ảnh chụp Swagger |
| 3 | Đo latency, RAM, tải đồng thời, timeout và cleanup | Báo cáo phần cứng, p50/p95, số model, số request |
| 4 | Backup PostgreSQL và uploads; restore sang môi trường riêng | Kiểm số record và mở lại ảnh; xác minh model bundle |
| 5 | Chốt bản ứng viên, sửa lỗi chặn demo | Test xanh và danh sách giới hạn sản phẩm đã thống nhất |

Giới hạn tính năng mới ngay đầu Tuần 7. Nếu core flow vẫn lỗi, dừng Grad-CAM hoặc policy động. Dashboard chỉ cần các số tổng và bộ lọc thời gian hữu ích; không thêm websocket hay phân tích xu hướng phức tạp.

### Tuần 8 phát hành và bảo vệ

| Ngày | Công việc | Kết quả |
| --- | --- | --- |
| 1 | Kiểm tra quyền truy cập, upload, cookie và secret | Danh sách lỗi nghiêm trọng bằng 0 trong phạm vi nghiệm thu |
| 2 | Kiểm tra ảnh thực tế và tập OOD cố định | Model card ghi rõ trường hợp thất bại và cách từ chối |
| 3 | Chuẩn hóa hướng dẫn chạy, cấu hình và dữ liệu demo | Một thành viên khác cài và chạy được từ tài liệu |
| 4 | Diễn tập demo; chuẩn bị bản dự phòng | Video và dữ liệu demo có quyền sử dụng; không dùng tài khoản thật |
| 5 | Gắn phiên bản phát hành và bàn giao | Mã nguồn, schema migration, model manifest, tài liệu, kết quả test |

### Quy tắc giảm phạm vi khi trễ

Nếu cuối Tuần 5 chưa có ảnh history và Farm flow đầy đủ, ưu tiên sửa core trước Proposal. Nếu ML chưa chứng minh OOD, vẫn chạy confidence rejection nhưng thông báo mức độ không chắc chắn; không đổi tên nó thành detector không phải lá. Nếu ensemble không cho lợi ích rõ ràng, giữ registry cả ba model và đề xuất mode nhẹ hơn dựa trên benchmark. Mọi thay đổi thành phần mode phải ghi policy version và thông báo người phụ trách FE.

Người phụ trách BE chịu trách nhiệm quyền và dữ liệu; ML chịu trách nhiệm artifact và phép đo; FE chịu trách nhiệm luồng thao tác và thông báo; nhóm cùng ký nhận kịch bản E2E và bản staging. Không kết luận FE chưa hoàn thành chỉ từ trạng thái một nhánh local cũ.

[PAGE]
## 6 Rủi ro và cách kiểm soát

| Rủi ro | Mức | Người xử lý | Biện pháp và bằng chứng |
| --- | --- | --- | --- |
| Confidence cao trên ảnh ngoài nhãn | Cao | ML và BE | Tập ID và OOD riêng; score có công thức; không đưa treatment khi policy từ chối |
| Ba model tăng tải nhưng không tăng chất lượng | Cao | ML | Đo đúng tổ hợp 2 và 3 model trên cùng test set; so macro F1 và latency |
| Nhiệm vụ Tuần 5 và 6 quá nhiều | Cao | Nhóm | Ưu tiên vận hành; P2 chỉ làm khi P0 đạt; đóng tính năng đầu Tuần 7 |
| Role đúng nhưng xem nhầm đối tượng | Cao | BE và FE | Test ownership cho API, ảnh, explanation; Admin giám sát qua namespace riêng |
| Xóa User kéo theo Farm và Scan | Cao | BE | Khóa tài khoản, không generic DELETE User; thử phục hồi trên database riêng |
| Duyệt đề xuất dở dang | Cao | BE | Lock và một commit cho content, status và audit; test hai lượt duyệt cùng lúc |
| Model active bị thiếu hoặc bundle sai | Cao | BE và ML | Validate, warm-up, transaction theo type; request giữ version đã chốt lúc bắt đầu |
| Ảnh và model mất khi deploy lại | Cao | BE | Persistent volume; kiểm backup ảnh; model immutable kèm checksum |
| Treatment hoặc threshold lịch sử thay đổi nghĩa | Vừa | BE | Snapshot policy; ghi rõ nội dung hiện hành hoặc bổ sung snapshot nội dung |
| Tăng RAM khi nhiều version ở cache | Vừa | BE | Giới hạn cache, giữ version in-flight, đo peak memory khi activate |
| Sai lọc ngày do timestamp không có timezone | Vừa | BE | Quy ước UTC; kiểm nguồn timezone trước migrate; test ranh giới ngày |
| Tài liệu mâu thuẫn với code | Vừa | Nhóm | Phân biệt hiện có và đề xuất; bỏ SQLite; lưu phiên bản OpenAPI và nguồn tham chiếu |

### Rủi ro dữ liệu ML

PlantDoc và dữ liệu thủ công đang được coi là các ảnh độc lập khi split. Điều này không chứng minh dữ liệu bị rò rỉ, nhưng cũng chưa loại trừ ảnh trùng hoặc các crop cùng ảnh gốc xuất hiện ở hai tập. ML cần kiểm tra duplicate và near-duplicate, lưu split manifest cố định, và đánh giá riêng từng nguồn. Độ chính xác tổng trên tập hỗn hợp không bảo đảm cùng mức chính xác ở đồng ruộng.

Ngưỡng thời gian phản hồi, RAM và tỷ lệ chấp nhận sai phải được nhóm đặt sau benchmark. Không sử dụng một con số tài nguyên hoặc chất lượng chưa đo như cam kết triển khai.

[PAGE]
## 7 Bàn giao ML theo mức cần thiết

### Để xác nhận chất lượng Tuần 3

Yêu cầu bộ artifact cố định kèm class order, preprocessing có interpolation và antialias, temperature đúng checkpoint, SHA 256, phiên bản thư viện và commit train. Backend đã có resize 224×224 không crop; vẫn cần vài ảnh chuẩn kèm logits hoặc xác suất tham chiếu để so kết quả ML và BE trong cùng điều kiện.

Yêu cầu metrics cho EfficientNet, MobileNet, ResNet và đúng hai tổ hợp Standard, Advanced. Dùng validation để chọn trọng số hoặc threshold rồi đánh giá test độc lập. Test hiện có 8582 ảnh và calibration có 8531 ảnh là hai tập khác nhau; số mẫu bằng nhau giữa các model chưa tự chứng minh cùng danh sách ảnh, nên cần split manifest hoặc hash.

Từ số chính xác trong metrics, ResNet dự đoán đúng hơn EfficientNet một ảnh trên 8582 ảnh. Không dùng chênh lệch accuracy đã làm tròn để khẳng định ResNet tốt hơn trong thực tế; cần xét macro F1, lỗi từng lớp và độ không chắc chắn của phép so sánh.

### Để chốt rejection và OOD

Người làm ML cần nêu score, chiều so sánh và tập dùng chọn 0.3. max_probability dưới 0.3 khác hoàn toàn 1 trừ max_probability trên 0.3. Temperature scaling hiệu chỉnh confidence trong điều kiện đánh giá, không xác nhận một ảnh là lá.

Gói tối thiểu gồm tập ID hợp lệ, ảnh ngoài 38 nhãn và ảnh không phải lá; danh sách ảnh dự đoán sai nhưng confidence cao; tỷ lệ ảnh ID bị từ chối và OOD được chấp nhận tại threshold đã chọn. AUROC hoặc FPR95 bổ sung khả năng so sánh nhưng không thay thế tỷ lệ lỗi tại threshold triển khai. Báo cáo riêng chất lượng ảnh và OOD gần nhãn khi có dữ liệu.

### Để triển khai các tuần sau

- Grad-CAM cần target layer, implementation thống nhất, ảnh heatmap mẫu đã kiểm tra và thời gian chạy trên CPU. ResNet phải dùng layer phù hợp, không hardcode features của MobileNet.
- Model Version cần bundle bất biến, model card, metrics, quy trình rollback và ảnh chuẩn kiểm warm-up. Đăng ký version mới khác với thêm kiến trúc mới.
- Deploy cần thời gian load, p50/p95 inference, RAM và VRAM, cấu hình phần cứng, đo từng mode khi chạy tuần tự và song song.
- Retraining nhãn mới là phạm vi sau MVP; đề xuất nội dung không tự mở rộng output model. Không bắt buộc chuyển ONNX hoặc tách thêm ba tập validation ngay nếu chưa có lợi ích và đủ dữ liệu.

Hiện tại không cần đợi toàn bộ nghiên cứu ML mới tiếp tục BE. Hợp đồng đầu vào, ownership, persistence, migration và monitoring vẫn triển khai được; phần chất lượng phải giữ trạng thái chờ nghiệm thu phù hợp.

[PAGE]
## 8 Nghiệm thu và vận hành

### Kịch bản bắt buộc

| Mã | Kịch bản | Kết quả mong đợi |
| --- | --- | --- |
| QA01 | Register chèn role hoặc Manager tạo admin | 422 và không tạo tài khoản sai quyền |
| QA02 | Logout hoặc đổi password rồi dùng token cũ | 401 với cả access và refresh; status kiểm ở mọi cửa vào |
| QA03 | Manager khác truy cập Farm hoặc Members | Bị từ chối; không lộ danh sách thành viên |
| QA04 | Guest Predict và User Predict | Guest không lưu; User tạo Scan và kết quả từng model trong cùng transaction |
| QA05 | Người khác lấy ảnh hoặc xóa Scan | Bị từ chối ở cả nội dung và ảnh |
| QA06 | Null trường bắt buộc khi cập nhật | 422; null field optional vẫn xóa đúng dữ liệu |
| QA07 | Hai Admin duyệt hoặc activate cùng lúc | Không có ghi dở dang hoặc hai version active cùng type |
| QA08 | Thiếu model, quá tải, timeout, DB lỗi | Lỗi có cấu trúc; không lộ path; không để ảnh hoặc record dang dở |
| QA09 | Restore database và uploads vào bản sao | Mở lại history, ảnh và liên kết model thành công |

Chạy từ thư mục backend với PostgreSQL local đang hoạt động. Các lệnh test dùng database riêng có hậu tố _test và có thể xóa, tạo lại database test; không cấu hình TEST_DATABASE_URL tới dữ liệu cần giữ.

```powershell
cd C:\Project\plant-disease\backend
.\.venv\Scripts\python.exe -m scripts.check_database
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m mypy app tests
```

Triển khai đầu tiên dùng một dịch vụ API và PostgreSQL, kèm volumes cho ảnh và model. Các process API đều có bản model cache và semaphore riêng; tăng workers có thể tăng RAM và tải inference. Đo trước khi tăng workers. Login và Guest predict cần giới hạn tần suất ở API hoặc proxy, HTTPS, cookie Secure và CORS theo đúng origin triển khai.

### Nguồn kiểm chứng

Code backend được rà soát tại HEAD 966a3bc và thay đổi preprocessing trong working tree ngày 07 tháng 09 năm 2026. Các file gốc: backend/app/api/v1/router.py; backend/app/models; backend/app/services; backend/tests; backend/alembic; backend/README.md. Tài liệu cũ trong docs/roadmap-8-weeks-revised.md và docs/backend-weeks1-4-implementation-report.md cần thay các mô tả SQLite và trạng thái chưa cập nhật bằng bộ tài liệu này sau khi nhóm duyệt.

Nguồn ML đã đối chiếu: https://github.com/Tad1232005/plant-disease/tree/7424a83/ml

Temperature scaling: Guo và cộng sự, On Calibration of Modern Neural Networks, 2017. https://proceedings.mlr.press/v70/guo17a.html

Nguyên tắc quyền theo đối tượng: OWASP API1 Broken Object Level Authorization. https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/
