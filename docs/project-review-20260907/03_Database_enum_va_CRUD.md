# Database enum và quy trình CRUD Plant Disease

Bộ tài liệu 3 trong 3 • Ngày 07 tháng 09 năm 2026 • Phiên bản đề xuất 1

## 1 Thiết kế dữ liệu hiện tại và hướng mở rộng

Database hiện dùng PostgreSQL với 8 bảng nghiệp vụ, ngoài bảng alembic_version do Alembic quản lý. Các cột được gọi là enum trong nghiệp vụ hiện dùng VARCHAR kết hợp CHECK, chưa dùng kiểu PostgreSQL ENUM. Đề xuất giữ cách này trong bản 8 tuần để giảm thay đổi không cần thiết; giá trị ở API và CHECK phải nhất quán.

Bản mục tiêu nếu có đầy đủ Proposal, Grad-CAM và audit sẽ có 11 bảng nghiệp vụ. Nếu Admin cấu hình mode là bắt buộc, thêm inference_policies và inference_policy_models, thành 13 bảng. Đây là thay đổi thiết kế được đề xuất, chưa phải schema đang chạy. Không cần dựng lại database từ đầu.

### Quan hệ chính và số lượng liên kết

| Bên cha | Quan hệ | Bên con và điều kiện |
| --- | --- | --- |
| User tạo tài khoản | 1 tới nhiều User | created_by ghi nguồn tạo, không tự cấp quyền đọc dữ liệu |
| Manager | 1 tới nhiều Farm | DB dùng farms.user_id; ORM và API gọi owner_id |
| Farm và Managed User | Nhiều tới nhiều | Qua farm_members; unique farm_id và user_id |
| User | 1 tới nhiều Scan | Mỗi Scan thuộc một user_id |
| Farm | 1 tới nhiều Scan | farm_id nullable; chỉ có nếu gắn Farm hợp lệ |
| Scan | 1 tới 0 đến 3 Top-K | scan_topk; unique scan_id và rank |
| Scan | 1 tới 1 đến 3 kết quả model mới | scan_model_results; dữ liệu legacy có thể chưa có |
| ModelVersion | 1 tới nhiều kết quả model | Version lịch sử bị RESTRICT khi có kết quả tham chiếu |
| Kết quả model | 1 tới nhiều explanation | ĐỀ XUẤT; theo target_label và algorithm_version |

FK bảo đảm bản ghi tồn tại; nó không tự xác minh owner là Manager hoặc user được Manager đó tạo. Các điều kiện liên bảng này thuộc service, kết hợp transaction và test. Không biểu diễn bằng CHECK đọc dữ liệu bảng khác.

Ký hiệu trong phần từ điển: PK là khóa chính, FK là khóa ngoại, NULL là được để trống, NN là bắt buộc. Kiểu TIMESTAMP hiện có không kèm timezone; TIMESTAMPTZ chỉ xuất hiện trong phần đề xuất.

[PAGE]
## 2 User Farm và thành viên

### users hiện có

| Cột hoặc nhóm cột | Kiểu và ràng buộc | Ý nghĩa |
| --- | --- | --- |
| id | INTEGER PK | Định danh tài khoản |
| username | VARCHAR 50 NN unique | Tên đăng nhập, hiện phân biệt hoa thường ở uniqueness |
| email | VARCHAR 100 NULL unique | Liên hệ; DB cho phép NULL |
| password_hash | VARCHAR 255 NN | Argon2; không xuất qua API |
| role | VARCHAR 20 NN CHECK | user, technician, manager, admin |
| full_name | VARCHAR 100 NULL | Tên hiển thị |
| created_by | INTEGER NULL FK users | Người tạo; SET NULL khi xóa vật lý người tạo |
| token_version | INTEGER NN default 0 | Tăng khi thu hồi phiên |
| created_at | TIMESTAMP NN | Thời điểm tạo hiện tại |

ĐỀ XUẤT thêm status VARCHAR CHECK active hoặc suspended, default active; suspended_at, suspended_by và suspension_reason nếu cần audit trực tiếp. CHECK token_version không âm và tăng bằng update nguyên tử. Khóa User giữ lại Farm, Scan và dấu vết; không cung cấp DELETE User trong MVP.

### farms hiện có

| Cột hoặc nhóm cột | Kiểu và ràng buộc | Ý nghĩa |
| --- | --- | --- |
| id | INTEGER PK | Định danh Farm |
| user_id | INTEGER NN FK users CASCADE | Owner vật lý; ORM và API dùng tên owner_id |
| name, location_text | VARCHAR 100 NN; VARCHAR 255 NULL | Tên và mô tả địa điểm |
| created_at, archived_at | TIMESTAMP NN; TIMESTAMP NULL | Tạo và archive |

### farm_members hiện có

| Cột hoặc nhóm cột | Kiểu và ràng buộc | Ý nghĩa |
| --- | --- | --- |
| id | INTEGER PK | Định danh membership |
| farm_id, user_id | INTEGER NN FK CASCADE | Liên kết Farm và User; unique theo cặp |
| added_by | INTEGER NULL FK users SET NULL | Manager thực hiện phân công |
| created_at | TIMESTAMP NN | Thời điểm gán |

Membership không có role riêng. Quyền user.role=user và user.created_by=manager.id được kiểm khi thêm. Đề xuất index user_id, farm_id để lấy Farm được giao. Xóa link không xóa tài khoản; archive Farm không xóa link hay Scan lịch sử.

[PAGE]
## 3 Nội dung bệnh và model version

### disease_info hiện có

| Cột hoặc nhóm cột | Kiểu và ràng buộc | Ý nghĩa |
| --- | --- | --- |
| id, label_key | INTEGER PK; VARCHAR 50 NN unique | ID nội dung và nhãn machine learning ổn định |
| disease_name | VARCHAR 100 NN | Tên hiển thị |
| description, treatment | TEXT NULL | Mô tả và hướng dẫn hiện hành |
| severity_level | VARCHAR 20 NN CHECK | low, medium, high; mức nội dung tham khảo |
| updated_by | INTEGER NULL FK users SET NULL | Người sửa cuối |
| created_at, updated_at | TIMESTAMP NN | Thời điểm tạo và cập nhật |
| is_active | BOOLEAN NN default true | Public khi active; DELETE API chỉ ẩn |

ĐỀ XUẤT content_version INTEGER NN default 1. Mỗi update, archive hoặc restore đều tăng version. Proposal pending chỉ được approve khi nội dung còn active và base_content_version khớp; nếu không trả 409. severity_level là thông tin nội dung bệnh, không phải mức tổn thương model đo trên ảnh.

### model_versions hiện có

| Cột hoặc nhóm cột | Kiểu và ràng buộc | Ý nghĩa |
| --- | --- | --- |
| id, version_name | INTEGER PK; VARCHAR 50 NN unique | Một bộ trọng số bất biến |
| model_type | VARCHAR 30 NN CHECK | Ba kiến trúc đã hỗ trợ |
| task | VARCHAR 40 NN default disease_classification | Hiện có default; chưa có CHECK task ở DB |
| file_path | VARCHAR 255 NN | Vị trí checkpoint |
| classes_path, temperature_path | VARCHAR 255 NULL | File mapping nhãn và calibration |
| temperature | FLOAT NN default 1, CHECK lớn hơn 0 | Hệ số chia logits |
| sha256 | VARCHAR 64 NULL | Hash toàn bộ bundle gồm checkpoint và metadata |
| accuracy, macro_f1, ece | FLOAT NULL CHECK từ 0 đến 1 | Metrics; không tự bảo đảm cùng test set |
| metrics_path | VARCHAR 255 NULL | Báo cáo đánh giá |
| is_active, is_enabled | BOOLEAN NN false; BOOLEAN NN true | Version dùng và version cho phép chạy |
| created_at, updated_at | TIMESTAMP NN | Thời điểm metadata |

Index unique có điều kiện trên model_type khi is_active=true đã có và đúng với ba model. Nó bảo đảm tối đa một active mỗi type, không bảo đảm luôn có active. Đề xuất CHECK is_active kéo theo is_enabled và kiểm tra temperature hữu hạn dương ở service. Không thay SHA hoặc checkpoint của version đã được Scan tham chiếu; đăng ký version mới.

[PAGE]
## 4 Scan và dữ liệu quyết định

### scans hiện có

| Cột hoặc nhóm cột | Kiểu và ràng buộc | Ý nghĩa |
| --- | --- | --- |
| id, user_id | INTEGER PK; INTEGER NN FK users CASCADE | Scan và chủ sở hữu |
| farm_id | INTEGER NULL FK farms SET NULL | Farm được gắn lúc tạo |
| image_path | VARCHAR 255 NN | Khóa file ảnh trong uploads |
| predicted_label | VARCHAR 50 NULL | Nhãn cuối, null khi bị từ chối |
| confidence | FLOAT NULL từ 0 đến 1 | Top-1 ensemble |
| is_valid_leaf | BOOLEAN NN | Field tương thích thể hiện policy chấp nhận |
| gradcam_path | VARCHAR 255 NULL | Cột cũ, chưa đủ biểu diễn nhiều model |
| model_version | VARCHAR 50 NULL | Chuỗi legacy, không phải FK |
| primary_model_version_id | INTEGER NULL FK SET NULL | Version đại diện; kết quả đầy đủ nằm ở bảng con |
| inference_mode | VARCHAR 20 NN CHECK | legacy, basic, standard, advanced |
| validation_status | VARCHAR 30 NN CHECK | accepted, low_confidence, ambiguous, model_error |
| rejection_reason | VARCHAR 50 NULL | Mã lý do, hiện chưa CHECK enum ở DB |
| agreement_status | VARCHAR 30 NN CHECK | single_model, agreed, disagreed, degraded |
| top1_top2_margin, ensemble_entropy | FLOAT NULL từ 0 đến 1 | Khoảng cách Top-1 Top-2 và entropy chuẩn hóa |
| js_divergence, ood_score | FLOAT NULL từ 0 đến 1 | Bất đồng và heuristic chẩn đoán |
| energy_score | FLOAT NULL | Chẩn đoán energy, không giới hạn 0 đến 1 |
| policy_version | VARCHAR 50 NULL | Chuỗi version; hiện thiếu snapshot cấu hình |
| created_at | TIMESTAMP NN | Thời điểm lưu |

### Hiệu chỉnh được đề xuất

Thêm inference_snapshot JSONB cho Scan mới: policy_version, công thức preprocessing hoặc version contract, ngưỡng hiệu lực, trọng số, yêu cầu min_success và các model_version_id đã chốt. Hiện đổi ngưỡng trong .env vẫn có thể giữ nguyên chuỗi ensemble-baseline-v1 nên cần snapshot để giải thích lịch sử chính xác.

Giữ validation_status là nguồn nghiệp vụ chính. Không hồi tố is_valid_leaf thành kết quả leaf detection. Top-K hoặc candidate của Scan bị từ chối chỉ phục vụ phân tích, không dùng như bệnh đã được xác nhận.

Nếu nhóm yêu cầu tái hiện nội dung lúc dự đoán, thêm disease_snapshot JSONB chứa label_key, content_version và phần nội dung đã hiển thị. Đây là lựa chọn khác với tiếp tục đọc hướng dẫn hiện hành. Snapshot legacy chưa biết giữ NULL.

[PAGE]
## 5 Kết quả con và quy tắc xóa

### scan_topk hiện có

| Cột hoặc nhóm cột | Kiểu và ràng buộc | Ý nghĩa |
| --- | --- | --- |
| id, scan_id | INTEGER PK; INTEGER NN FK CASCADE | Thuộc Scan |
| label | VARCHAR 50 NN | Nhãn trong output ensemble |
| confidence | FLOAT NN từ 0 đến 1 | Xác suất của nhãn |
| rank | INTEGER NN CHECK 1 đến 3 | Unique scan_id và rank |

### scan_model_results hiện có

| Cột hoặc nhóm cột | Kiểu và ràng buộc | Ý nghĩa |
| --- | --- | --- |
| id, scan_id | INTEGER PK; INTEGER NN FK CASCADE | Kết quả thuộc Scan |
| model_version_id | INTEGER NN FK model_versions RESTRICT | Checkpoint thực dùng; unique cặp scan và model |
| execution_order | INTEGER NN CHECK 1 đến 3 | Thứ tự cấu hình, không phải thứ tự thread hoàn thành |
| predicted_label | VARCHAR 50 NULL | Nhãn riêng của model |
| confidence, top1_top2_margin, entropy | FLOAT NULL từ 0 đến 1 | Chỉ số riêng |
| energy_score | FLOAT NULL | Energy riêng |
| accepted | BOOLEAN NN default false | Hiện dựa trên confidence riêng, không đồng nghĩa ensemble accepted |
| latency_ms | FLOAT NULL không âm | Thời gian xử lý model |
| error_code | VARCHAR 50 NULL | inference_failed hoặc mã lỗi được chuẩn hóa |
| topk_json | TEXT NULL | JSON serialize của Top-K, hiện chưa phải JSONB |
| created_at | TIMESTAMP NN | Thời điểm ghi |

Không có FK từ nhãn của Scan hoặc Top-K tới disease_info. Nhãn của model tồn tại độc lập với nội dung có thể sửa hoặc ẩn. Điều này cũng cho phép kết quả dự đoán còn tồn tại khi nội dung bệnh chưa được biên tập.

### Xóa vật lý khác với API DELETE

User bị xóa vật lý có thể cascade Farm và Scan. Farm bị xóa vật lý cascade membership và đặt farm_id của Scan thành NULL. Vì thế ứng dụng nên khóa User, archive Farm và ẩn Disease thay vì xóa các đối tượng này. Xóa Scan chủ động được phép và cascade Top-K, model results, explanation đề xuất; phải dọn file tương ứng.

ModelVersion đã có scan_model_results tham chiếu bị RESTRICT. Primary FK trên scans là SET NULL không có nghĩa version đó luôn xóa được. Không mở generic DELETE model trong bản 8 tuần. Các khóa creator hoặc editor SET NULL làm mất tên liên kết nếu xóa tài khoản vật lý, là thêm lý do giữ account bị khóa.

[PAGE]
## 6 Enum và miền giá trị cần thống nhất

Giữ tên key tiếng Anh ổn định trong API và database, dịch nhãn hiển thị ở FE. Một miền dùng VARCHAR CHECK không có nghĩa mọi string trong database đều là enum.

| Miền | Giá trị | Phạm vi và quy tắc |
| --- | --- | --- |
| UserRole | user, technician, manager, admin | HIỆN CÓ API và DB; không có guest hoặc managed_user |
| SeverityLevel | low, medium, high | HIỆN CÓ; không có critical và không đo severity ảnh |
| ModelType | mobilenet_v2, efficientnet_b0, resnet50 | HIỆN CÓ; thêm kiến trúc cần code và migration |
| InferenceMode | basic, standard, advanced | HIỆN CÓ; DB còn legacy cho dữ liệu cũ |
| RequestedMode | auto, basic, standard, advanced | HIỆN CÓ API-only; auto được resolve trước khi ghi |
| ValidationStatus | accepted, low_confidence, ambiguous, model_error | HIỆN CÓ; không tự thêm not_a_leaf nếu chưa có bằng chứng |
| AgreementStatus | single_model, agreed, disagreed, degraded | HIỆN CÓ; disagreed vẫn có thể accepted nếu policy cho phép |
| FarmAssignmentStatus | not_applicable, not_requested, assigned, not_allowed | HIỆN CÓ API-only; lưu farm_id thực tế |
| RejectionReason | confidence_below_threshold, top1_top2_margin_too_small, model_disagreement_too_high | Mã do code hiện tạo; VARCHAR chưa CHECK tại DB |
| ModelErrorCode | inference_failed | Mã hiện có ở kết quả model; response lỗi toàn request là HTTP 503 hoặc 504 |
| UserStatus | active, suspended | ĐỀ XUẤT; kiểm ở login, refresh, bearer |
| ProposalStatus | pending, approved, rejected | ĐỀ XUẤT; không trộn trạng thái retraining |
| ProposalType | update_content | ĐỀ XUẤT MVP; nhãn mới ở backlog riêng |
| ExplanationMethod | gradcam | ĐỀ XUẤT; version thuật toán nằm ở cột riêng |
| ExplanationStatus | succeeded, failed | ĐỀ XUẤT đồng bộ; queued hoặc running chỉ thêm khi thật sự có worker |

### Miền động phải lưu bằng dữ liệu

Model version, danh sách nhãn và thành phần mode không nên biến thành hàng trăm giá trị enum cố định. model_versions lưu version; classes.json trong bundle xác định output. Nếu có policy động, bảng con lưu thành phần và weight. Inference policy mode vẫn thuộc ba tên được hỗ trợ.

CHECK có thể chấp nhận NULL nếu biểu thức không ra false; vì thế cột bắt buộc vẫn cần NOT NULL. Ràng buộc thuộc nhiều bảng như cùng Manager phải kiểm ở service hoặc thiết kế khóa phù hợp, không dùng CHECK đọc bảng khác. Nguồn: PostgreSQL 17 Constraints, https://www.postgresql.org/docs/17/ddl-constraints.html

[PAGE]
## 7 Bảng đề xuất cho workflow và audit

### disease_proposals

Thêm trong Tuần 6 để Technician gửi sửa nội dung mà Admin kiểm soát xuất bản. Bảng dùng id INTEGER PK; proposer_id FK users RESTRICT; label_key VARCHAR 50; proposal_type CHECK update_content; base_content_version INTEGER; disease_name VARCHAR 100; description và treatment TEXT nullable; severity_level CHECK low medium high; status CHECK pending approved rejected; reviewer_id FK users SET NULL; review_note TEXT; created_at và reviewed_at TIMESTAMPTZ.

Các field bắt buộc và nullable phải khớp schema Disease Info. Khi pending thì reviewer_id và reviewed_at rỗng. Khi reviewed phải có reviewed_at và thông tin reviewer theo chính sách giữ account. Reject bắt buộc review_note không rỗng. Index proposer_id, created_at, id cho mine; status, created_at, id cho queue Admin.

Không có generic update hoặc delete bản đã duyệt. Lock proposal trước: quyết định đã trùng yêu cầu thì trả record, không kiểm lại revision hoặc ghi thêm; quyết định đối nghịch trả 409. Chỉ pending mới kiểm nội dung còn active và base_content_version trước approve. Archive nội dung cũng tăng version để chặn đề xuất cũ.

### scan_explanations

Thêm khi Grad-CAM còn trong phạm vi. Bảng dùng id INTEGER PK; scan_model_result_id FK CASCADE; target_label VARCHAR 50; method CHECK gradcam; algorithm_version VARCHAR 50; status CHECK succeeded failed; requested_by FK users SET NULL; artifact_key VARCHAR 255 nullable; error_code VARCHAR 50 nullable; created_at và completed_at TIMESTAMPTZ.

Unique theo scan_model_result_id, target_label, method, algorithm_version để cache kết quả. Trạng thái succeeded bắt buộc có artifact_key; failed có error_code và không trả ảnh như thành công. Lần retry phải serialize theo cùng khóa để không tạo nhiều heatmap cạnh tranh. Bản chạy đồng bộ không cần bảng job hay hứa hẹn background task bền vững qua restart.

Version model kế thừa từ scan_model_results. Quyền đọc kiểm theo Scan gốc và role Technician hoặc Manager. Delete Scan cascade record explanation; file ảnh cần service dọn riêng vì FK không xóa được filesystem.

### audit_events

Thêm từ Tuần 5 để ghi hoạt động quản trị. Bảng dùng id BIGINT PK; actor_id FK users SET NULL; action VARCHAR 80; resource_type VARCHAR 50; resource_id VARCHAR 100; outcome VARCHAR 20; request_id VARCHAR 100 nullable; metadata JSONB đã lọc; created_at TIMESTAMPTZ. Index theo created_at và resource_type, resource_id, created_at.

Ghi đổi status, review nội dung, activate model và truy cập ảnh qua API Admin khi cần giám sát. Ứng dụng chỉ append; không mở API sửa hoặc xóa audit. Metadata không chứa mật khẩu, token, hash mật khẩu hoặc dữ liệu ảnh. AuditEvents ghi ai làm gì; ScanModelResult ghi model đã dự đoán thế nào, hai bảng phục vụ mục đích khác nhau.

[PAGE]
## 8 Hai bảng tùy chọn cho policy của mode

Nếu Admin cần chỉnh thành phần Basic Standard Advanced ngay trong bản 8 tuần, bổ sung hai bảng dưới đây và ba API policy ở tài liệu 2. Nếu chưa triển khai, giữ cấu hình code hiện tại và ghi rõ Admin chưa có quyền chỉnh mode qua giao diện.

### inference_policies

Mỗi record là một revision bất biến cho một mode: id INTEGER PK; version_name VARCHAR 50 unique; mode CHECK basic standard advanced; confidence_threshold, margin_threshold, js_threshold FLOAT trong 0 đến 1; min_success INTEGER từ 1 đến 3; allow_degraded BOOLEAN; is_active BOOLEAN; created_by FK users; created_at TIMESTAMPTZ. Unique có điều kiện trên mode khi active bảo đảm tối đa một revision active cho một mode.

Không sửa nội dung revision đang active; tạo revision mới rồi activate. Quyền mode của role vẫn cố định ở service trong bản tối giản. Role, mode và quyền trả phí là ba khái niệm khác nhau; thanh toán chưa thuộc triển khai này.

### inference_policy_models

policy_id FK inference_policies RESTRICT; model_type CHECK ba kiến trúc; execution_order INTEGER từ 1 đến 3; weight FLOAT hữu hạn dương. PK hoặc UNIQUE policy_id và model_type; UNIQUE policy_id và execution_order. Service xác minh policy có 1 đến 3 model khác nhau, min_success không lớn hơn số model, tổng trọng số hữu hạn và chuẩn hóa đúng khi inference.

Policy tham chiếu model_type, còn request resolve một active ModelVersion cho mỗi type lúc bắt đầu. Điều này giữ đúng quy tắc active theo kiến trúc đã có. Các model phải cùng class order và preprocessing tương thích. Policy mới không được active nếu thiếu model cần thiết.

### Liên kết với Scan và xử lý cạnh tranh

Thêm scans.inference_policy_id NULL FK RESTRICT và inference_snapshot JSONB. Snapshot giữ version policy, các ngưỡng, trọng số, min_success và model_version_id đã thực dùng. Legacy có thể để NULL. Một request đã chọn policy và model IDs không chuyển sang version mới giữa lượt xử lý.

Activate policy serialize theo mode, xác minh mọi dependency và commit một lần. Activate model serialize theo model_type. Index unique là lớp chống lỗi cuối; khóa transaction bảo đảm hai Admin không ghi đè ý định của nhau. Nếu version mới có class order khác các model còn lại, phải bị chặn đối với mode ensemble đang phụ thuộc vào nó.

### Tác động tới phạm vi

Hai bảng này giải quyết yêu cầu cấu hình mode, nhưng kéo theo thay đổi cache, validation, capability response, snapshot và test cạnh tranh. Nếu giữ chúng ở P0, phải giảm một tính năng P1 khác hoặc tăng thời gian; không coi đây là việc thêm vài record trong model_versions.

[PAGE]
## 9 Quy trình CRUD và transaction

| Đối tượng | Create và Read | Update và Delete |
| --- | --- | --- |
| User | Public: role=user, created_by=NULL; cấp tài khoản: role theo actor, created_by=actor.id | Đổi password hoặc status bằng API chuyên biệt; tăng token_version; không hard-delete |
| Farm | Manager tạo; owner server gán; list scoped owner | Field cho phép; không đổi owner; archive để giữ Scan |
| Member | Kiểm Farm owner, role user và created_by rồi insert unique | Không generic update; remove link; lịch sử đã gắn Farm giữ nguyên |
| Disease Info | Admin tạo; label ổn định; public read chỉ active | Field whitelist, revision; delete ẩn; restore theo contract hiện tại |
| Proposal | Technician submit pending; mine theo creator; Admin queue | Approve hoặc reject với khóa và version; record reviewed bất biến |
| Model Version | Register artifact bất biến; Admin list | Activate cùng type; rollback bằng version cũ; giữ bundle lịch sử |
| Scan | Chỉ Predict tạo; User đọc chính mình | Không sửa label hoặc confidence; chủ Scan xóa và dọn artifact |
| Explanation | Tạo từ model result đúng version; cache khóa duy nhất | Đọc có quyền; failed được retry; dọn cùng Scan |

### Phân biệt thiếu field với null

Request cập nhật không gửi name thì giữ name cũ. Gửi name=null, disease_name=null hoặc severity_level=null phải nhận 422 vì các cột này không nullable. Gửi location_text=null, description=null hoặc treatment=null được phép xóa giá trị. Chỉ dùng exclude_unset không đủ xử lý điều kiện này; validator phải phân biệt field không có và field được gửi null.

### Transaction cho Predict

Đọc quyền và model version trước công việc nặng; inference không giữ transaction ghi lâu. Khi persist phải kiểm lại điều kiện có thể thay đổi như membership hoặc status, ghi ảnh tạm rồi đổi tên an toàn, insert Scan và các kết quả con, commit. Nếu DB lỗi phải rollback và dọn ảnh vừa tạo. File và PostgreSQL không có chung transaction; cần cleanup có thể retry cho lỗi filesystem sau commit.

### Transaction cho review và activation

Approve cần lock proposal cùng nội dung, kiểm revision, cập nhật disease_info, status và audit, rồi commit một lần. CRUD được gọi bên trong không được tự commit. Activate cần warm-up trước và lock theo kiến trúc hoặc mode khi đổi active, ghi audit cùng transaction. Nếu có lỗi, cấu hình active cũ vẫn sẵn sàng cho request mới.

[PAGE]
## 10 Migration và kiểm soát thay đổi

Schema hiện tại do Alembic quản lý. Không sửa migration đã chạy để đưa thiết kế mới vào database hiện có. File SQL export là bản chụp để bàn giao hoặc backup; pgAdmin không thay thế lịch sử migration.

### Trình tự đề xuất

1. Backup PostgreSQL, uploads và manifest model; thử restore sang database riêng. Kiểm tra record, ảnh và tham chiếu trước khi coi backup hợp lệ.

2. Thêm status User default active, content_version, snapshot nullable và các bảng mới bằng migration tiến tới. Giữ physical farms.user_id, các field legacy và response cũ trong giai đoạn tương thích.

3. Backfill những dữ liệu có căn cứ. Không điền threshold hoặc treatment lịch sử bằng giá trị hiện tại rồi ghi như dữ liệu gốc. Đọc và ghi phải xử lý NULL của legacy.

4. Trước khi thêm CHECK active kéo theo enabled, tìm và xử lý record vi phạm. Trước khi chuẩn hóa username hoặc email không phân biệt hoa thường, kiểm trùng có thể phát sinh. Test migration trên bản sao có dữ liệu.

5. Khi chuyển TIMESTAMP sang TIMESTAMPTZ, xác minh timezone lịch sử. Chỉ dùng AT TIME ZONE với múi giờ đã được chứng minh; không đoán mọi record cũ đều UTC. API mới thống nhất ISO 8601 UTC và test bộ lọc ngày.

6. Deploy code đọc được schema mới, chạy integration test và test cạnh tranh. Không downgrade database phát triển về base để test. Rollback ứng dụng hoặc migration sửa tiến tới thường phù hợp hơn downgrade có thể mất dữ liệu.

### Index và điều kiện cần kiểm tra

| Truy vấn | Index đề xuất | Lưu ý |
| --- | --- | --- |
| History User | scans user_id, created_at DESC, id DESC | Thay vì phụ thuộc index rời; kiểm EXPLAIN trên dữ liệu phù hợp |
| Dashboard Farm | scans farm_id, created_at DESC, id DESC | Chỉ Scan gắn Farm; filter khoảng thời gian |
| Admin rejection | scans validation_status, created_at DESC, id DESC | Không thêm mọi tổ hợp index khi chưa có truy vấn thực |
| Farm của User | farm_members user_id, farm_id | Bù cho unique hiện bắt đầu bằng farm_id |
| Proposal pending và mine | status hoặc proposer_id, created_at, id | Phân trang và sort ổn định |

Nguồn schema: backend/app/models và backend/alembic/versions tại ngày rà soát. Quy tắc CHECK và unique: PostgreSQL 17 Constraints, https://www.postgresql.org/docs/17/ddl-constraints.html. Đặc tính enum native: https://www.postgresql.org/docs/17/datatype-enum.html. Lựa chọn VARCHAR CHECK ở đây là quyết định giảm phạm vi migration cho dự án này.
