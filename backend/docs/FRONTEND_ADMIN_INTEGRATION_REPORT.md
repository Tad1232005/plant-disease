# BÁO CÁO ĐÁNH GIÁ HIỆN TRẠNG KẾT NỐI API & GIAO DIỆN FRONTEND / ADMIN

- **Dự án:** Hệ thống Chẩn đoán Bệnh Cây trồng (Plant Disease Detection System)
- **Thời gian lập báo cáo:** 10/2026
- **Phạm vi khảo sát:** Client App (`frontend/`), Admin Portal (`admin/`), Backend REST APIs (`backend/`)
- **Trạng thái khảo sát:** Read-only / Code Audit (Không sửa đổi mã nguồn)

---

## 1. TỔNG QUAN HIỆN TRẠNG HỆ THỐNG

Sau khi rà soát toàn bộ các route điều hướng (`App.jsx`), các tầng dịch vụ API client (`src/api/`, `src/services/`) và các component trang giao diện (`src/pages/`):

| Phân hệ | Tổng số trang/luồng | Đã kết nối API thật | Bị lệch Endpoint / Lỗi gọi | Còn dùng Mock / LocalStorage | Mức độ hoàn thiện |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Frontend App** (`frontend/`) | 8 trang chính | 6 luồng | **2 lỗi** | **3 trang** | ~60% |
| **Admin Portal** (`admin/`) | 7 trang chính | 4 luồng | **1 lỗi** | **2 trang** | ~50% |

> **Nhận xét chung:**
> Trục nghiệp vụ xương sống quan trọng nhất đã chạy thông suốt với Backend: **Xác thực JWT $\rightarrow$ Chẩn đoán qua mạng nơ-ron Ensemble 2 tầng $\rightarrow$ Lưu lịch sử chẩn đoán $\rightarrow$ Thống kê báo cáo Farm $\rightarrow$ Quản trị phiên bản Model AI**.
> Tuy nhiên, một số trang nhánh (Thư viện bệnh, Quản lý Farm, Duyệt đề xuất) vẫn đang lưu tạm trong trình duyệt hoặc dùng file dữ liệu mẫu (`demoData.js`) dù Backend đã có sẵn API đầy đủ.

---

## 2. DANH SÁCH LỖI KẾT NỐI API (CRITICAL MISMATCHES)

Đây là những chức năng đã có code gọi API nhưng **gọi sai cấu trúc URL hoặc sai HTTP Method** của Backend, dẫn đến lỗi runtime (`404 Not Found` hoặc `405 Method Not Allowed`):

### 2.1. Frontend – Tra cứu bản đồ nhiệt Grad-CAM
- **Vị trí code:** `frontend/src/api/predict.js` (dòng 15–24)
- **Frontend đang gọi:** `POST /api/v1/predict/explain`
- **Thực tế Backend:** Backend **không có route** `/predict/explain`. Backend quản lý Grad-CAM theo ca quét đã lưu:
  - `GET /api/v1/scans/{scan_id}/gradcam`: Lấy ảnh heatmap đã render
  - `POST /api/v1/scans/{scan_id}/gradcam`: Yêu cầu render lại heatmap
- **Hậu quả:** Khi người dùng bấm nút *"Xem giải thích Grad-CAM"* trên `ScanPage.jsx`, request luôn nhận mã `404` và buộc phải rơi vào hàm vẽ canvas mô phỏng tạm thời.
- **Giải pháp khắc phục:** Cập nhật hàm gọi API nhận `scanId` và gọi `GET /api/v1/scans/${scanId}/gradcam`.

### 2.2. Frontend – Xóa thành viên khỏi Nông trại
- **Vị trí code:** `frontend/src/api/managedUsers.js` (dòng 11–15)
- **Frontend đang gọi:** `DELETE /api/v1/farms/${farmId}/members` kèm Request Body `{ user_id }`
- **Thực tế Backend:** Endpoint router quy định: `DELETE /api/v1/farms/{farm_id}/members/{user_id}` (nhận `user_id` trực tiếp qua Path Parameter, không nhận body).
- **Hậu quả:** Khi quản lý nông trại bấm xóa nhân sự, server trả về `405 Method Not Allowed` hoặc `422 Unprocessable Entity`.
- **Giải pháp khắc phục:** Sửa URL gọi thành:
  ```javascript
  export const removeFarmMember = (farmId, userId) => 
    client.delete(`/farms/${farmId}/members/${userId}`);
  ```

### 2.3. Admin – Phê duyệt & Từ chối Đề xuất Bệnh
- **Vị trí code:** `admin/src/services/proposals.js` (dòng 5–12)
- **Admin đang gọi:** `PUT /api/v1/admin/disease-proposals/${id}` với payload `{ status: 'approved' | 'rejected', review_note }`
- **Thực tế Backend:** Backend phân tách rõ ràng thành 2 action endpoints:
  - `PUT /api/v1/admin/disease-proposals/{id}/approve`
  - `PUT /api/v1/admin/disease-proposals/{id}/reject`
- **Hậu quả:** Khi Quản trị viên bấm Duyệt hoặc Từ chối đề xuất, request bị trả về `404 Not Found`.
- **Giải pháp khắc phục:** Tách `reviewProposal` thành 2 hàm `approveProposal(id, note)` và `rejectProposal(id, note)` gọi đúng 2 endpoint trên.

---

## 3. CÁC TRANG CÒN DÙNG MOCK / LOCALSTORAGE (CHƯA NỐI API THẬT)

### 3.1. Phía Frontend Client (`frontend/`)

1. **Trang Quản lý Nông trại (`FarmsPage.jsx`):**
   - *Hiện trạng:* File `frontend/src/api/farms.js` đã viết sẵn đầy đủ các hàm `list()`, `create()`, `update()`, `remove()`. Tuy nhiên component `FarmsPage.jsx` hoàn toàn chưa import mà dùng `localStorage.getItem('plantcare_farms')`.
   - *Hạn chế:* Các nông trại tạo trên máy này không lưu về CSDL máy chủ, dẫn đến không đồng bộ được ca quét vào Farm trong database.

2. **Trang Thư viện Bệnh cây (`DiseaseLibraryPage.jsx`):**
   - *Hiện trạng:* File `frontend/src/api/diseases.js` đã có hàm `list()` (`GET /disease-info`). Trang hiện tại lại import trực tiếp mảng tĩnh `initialDiseases` từ `demoData.js`.
   - *Hạn chế:* Khi admin thêm/sửa bệnh cây trong database, nông dân xem thư viện bệnh sẽ không thấy dữ liệu cập nhật mới nhất.

3. **Bảng tin hoạt động (`DashboardPage.jsx`):**
   - *Hiện trạng:* Các chỉ số thống kê tuần, tỷ lệ nhận diện đang gán mảng cứng `[45, 68, 54, 82, ...]` và lấy ca quét gần nhất từ `localStorage`.
   - *Cần nối:* Gọi `GET /api/v1/stats/overview` và `GET /api/v1/scans/history?limit=5`.

4. **Dropdown chọn Farm khi Chẩn đoán (`ScanPage.jsx`):**
   - *Hiện trạng:* Danh sách chọn Nông trại để gắn ảnh quét đọc từ `localStorage`. Cần chuyển sang gọi API `GET /api/v1/farms` để người dùng chọn Farm thật từ database.

### 3.2. Phía Admin Portal (`admin/`)

1. **Trang Quản lý Danh mục Bệnh (`DiseaseManagementPage.jsx`):**
   - *Hiện trạng:* Toàn bộ thao tác CRUD đang thực hiện trên mảng state nội bộ nạp từ `initialDiseases` (`demoData.js`).
   - *Cần nối:* Kết nối bộ API `GET/POST/PUT/DELETE /api/v1/disease-info` đã có sẵn trên Backend.

2. **Trang Giám sát Nông trại (`FarmsPage.jsx`):**
   - *Hiện trạng:* Danh sách nông trại toàn hệ thống nạp từ `initialFarms` (`demoData.js`).
   - *Cần nối:* Kết nối API quản trị nông trại toàn hệ thống của Backend.

3. **Trang Duyệt Đề xuất Bệnh (`DiseaseProposalsPage.jsx`):**
   - *Hiện trạng:* Đang nạp danh sách khởi tạo từ `initialProposals` (mock), chưa fetch từ `GET /api/v1/admin/disease-proposals`.

---

## 4. CHI TIẾT CÁC PHẦN ĐÃ KẾT NỐI API THẬT HOẠT ĐỘNG TỐT

### 4.1. Phía Frontend
- **Authentication:** `POST /api/v1/auth/login`, `POST /api/v1/auth/register` hoạt động hoàn hảo. Token được lưu vào `localStorage`, tự động gắn vào Header `Authorization: Bearer <token>` thông qua Axios Interceptor.
- **Inference Chẩn đoán (`ScanPage.jsx`):** Gửi ảnh multipart/form-data đến `POST /api/v1/predict`. Nhận đầy đủ kết quả: nhãn bệnh, độ tin cậy, model phiên bản, validation status, OOD score, biện pháp khắc phục.
- **Lịch sử Chẩn đoán (`HistoryPage.jsx`):** Gọi `GET /api/v1/scans/history` và `GET /api/v1/scans/{id}` chuẩn chỉnh.
- **Báo cáo Thống kê Farm (`FarmDashboardPage.jsx`):** Gọi `GET /api/v1/stats/farm/{farm_id}` vẽ biểu đồ phân bố dịch bệnh chính xác.
- **Quản lý Thành viên Farm (`ManagedUsersPage.jsx`):** Gọi `GET /api/v1/manager/users` và `POST /api/v1/farms/{farm_id}/members` thêm nhân sự vào nông trại thành công.
- **Đề xuất Bệnh mới (`DiseaseProposalsPage.jsx`):** Nông dân gửi ảnh và mô tả đề xuất bệnh mới qua `POST /api/v1/disease-proposals`, xem đề xuất của mình qua `GET /api/v1/disease-proposals/mine`.

### 4.2. Phía Admin
- **Quản lý Tài khoản (`UsersPage.jsx`):** Gọi `GET /api/v1/admin/users` tải danh sách người dùng thật từ CSDL.
- **Quản trị Phiên bản Model AI (`ModelVersionsPage.jsx`):** Đã kết nối đầy đủ:
  - `GET /api/v1/admin/model-versions`
  - `POST /api/v1/admin/model-versions/register`
  - `POST /api/v1/admin/model-versions/{id}/activate`
- **Giám sát Sức khỏe Hệ thống (`SystemStatsPage.jsx`):** Gọi chuẩn `/health/live`, `/health/ready`, `/predict/capabilities` hiển thị thông tin GPU/CPU, RAM, model đang nạp.
- **Dashboard Quản trị (`AdminDashboardPage.jsx`):** Gọi `GET /api/v1/stats/admin/overview` lấy số liệu tổng quát toàn sàn.

---

## 5. CÁC TRANG GIAO DIỆN CÒN THIẾU TRONG TOÀN BỘ HỆ THỐNG

Đối chiếu với năng lực Backend và yêu cầu vận hành thực tế:

1. **Trang Hồ sơ Cá nhân & Đổi mật khẩu (`ProfilePage` / `ChangePassword`):**
   - *Backend hỗ trợ:* `POST /api/v1/auth/change-password` và `GET /api/v1/me`.
   - *Hiện trạng:* Cả Frontend và Admin đều chưa có màn hình/modal cho phép người dùng xem thông tin tài khoản, cập nhật tên hoặc đổi mật khẩu khi có nhu cầu.

2. **Trang Chi tiết Ca quét Độc lập (`/app/scans/:id`):**
   - *Hiện trạng:* Hiện tại xem chi tiết kết quả quét chỉ mở qua Modal popup trong `HistoryPage.jsx`.
   - *Đề xuất:* Cần có URL định tuyến riêng (`/app/scans/:id`) để người dùng có thể lưu link, chia sẻ kết quả cho kỹ sư hoặc in phiếu chẩn đoán.

3. **Trang Nhật ký Hoạt động Quản trị (`AuditLogsPage` - Admin):**
   - *Backend hỗ trợ:* Bảng `audit_logs` tự động ghi nhận mọi thao tác nhạy cảm: kích hoạt model ML mới, duyệt đề xuất bệnh, phân quyền tài khoản, xóa nông trại.
   - *Hiện trạng:* Giao diện Admin chưa có trang để Quản trị viên tra cứu các sự kiện bảo mật này.

4. **Bản đồ Cảnh báo Vùng Dịch (Disease Outbreak Heatmap):**
   - *Hiện trạng:* Đã có tọa độ và thông tin nông trại nhưng chưa có giao diện trực quan hóa dịch bệnh trên bản đồ địa lý theo thời gian thực.

---

## 6. KẾ HOẠCH HÀNH ĐỘNG KHUYẾN NGHỊ (ACTION CHECKLIST)

Khi được phép chỉnh sửa mã nguồn Frontend và Admin, thứ tự ưu tiên xử lý gồm:

- [ ] **Ưu tiên 1 (Sửa lỗi kết nối):**
  1. Sửa `frontend/src/api/predict.js`: Chuyển Grad-CAM sang `GET /scans/{id}/gradcam`.
  2. Sửa `frontend/src/api/managedUsers.js`: Chuyển `user_id` vào Path parameter `DELETE /farms/${farmId}/members/${userId}`.
  3. Sửa `admin/src/services/proposals.js`: Tách thành 2 hàm gọi `/approve` và `/reject`.

- [ ] **Ưu tiên 2 (Thay thế Mock data bằng API thật):**
  1. `frontend/src/pages/app/FarmsPage.jsx`: Import và gọi `farmsApi.list()`, `create()`, `remove()`.
  2. `frontend/src/pages/app/DiseaseLibraryPage.jsx`: Gọi `diseasesApi.list()`.
  3. `admin/src/pages/DiseaseManagementPage.jsx`: Nối API CRUD `/api/v1/disease-info`.
  4. `admin/src/pages/FarmsPage.jsx`: Nối API danh sách nông trại.

- [ ] **Ưu tiên 3 (Bổ sung giao diện còn thiếu):**
  1. Xây dựng trang Hồ sơ cá nhân / Đổi mật khẩu cho Frontend và Admin.
  2. Xây dựng trang xem Audit Log cho Admin Portal.
