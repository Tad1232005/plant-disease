# PlantCare AI Frontend người dùng

Frontend React (Vite) cho hệ thống nhận diện bệnh lá cây, được nâng cấp từ code ban đầu của repo `Tad1232005/plant-disease`.

## Chức năng đã hoàn thành

### Guest, giao diện di động, VI/EN và Dark Mode

- Route công khai `/guest/scan`: chụp/tải ảnh và xem kết quả mà không cần đăng nhập.
- Guest không thấy Farm, lịch sử hay Grad-CAM và kết quả Guest không được ghi vào localStorage.
- Nút chuyển VI/EN và Light/Dark được lưu theo trình duyệt.
- Header, drawer và bottom navigation responsive cho điện thoại; input camera dùng camera sau khi thiết bị hỗ trợ.
- Ma trận quyền được áp dụng đúng: User tự đăng ký; Manager chỉ tạo Managed User; Admin chỉ tạo Technician/Manager.

### Tuần 1 — Khởi động & Auth

- 3 persona chính: Nông dân, Kỹ thuật viên, Quản lý trang trại.
- Landing page và wireframe hoàn chỉnh theo tone xanh lá + trắng sáng.
- React Router và route bảo vệ theo đăng nhập/role.
- Auth Context gọi đúng API:
  - `POST /api/v1/auth/register`
  - `POST /api/v1/auth/login`
  - `GET /api/v1/auth/me`
- Trang chẩn đoán gọi `POST /api/v1/predict`, upload/drag-drop ảnh, kiểm tra định dạng và dung lượng.
- Hai component dùng chung: `DataTable` và `CrudForm`.

### Tuần 2 — Component nền tảng

- `DataTable`: tìm kiếm, sắp xếp, phân trang, custom cell và action.
- `CrudForm`: tạo form từ cấu hình field, React Hook Form + Zod validation.
- Farm Management: CRUD giao diện, thống kê, tìm kiếm; lưu demo bằng localStorage.
- Thư viện bệnh cho người dùng thường.
- Service sẵn sàng nối API `/farms` và `/disease-info`.

### Tuần 3 — Predict Core

- Chọn ảnh từ thư viện, kéo thả hoặc chụp trực tiếp bằng camera sau trên điện thoại.
- Kiểm tra JPG/PNG/WEBP, giới hạn 8 MB và xem trước ảnh.
- Gọi `POST /api/v1/predict`, hiển thị nhãn, độ tin cậy và top 3 dự đoán.
- Gắn kết quả với khu vực/trang trại và lưu lịch sử gần nhất trên trình duyệt.

### Tuần 4 — Managed User & Farm Members

- Route Manager riêng: `/app/managed-users`.
- Danh sách Managed User dùng lại `DataTable`.
- Form Manager chỉ tạo Managed User (role `user`) và gán vào Farm bằng `CrudForm`.
- Chuẩn bị service cho:
  - `GET/POST /api/v1/manager/users`
  - `GET/POST/DELETE /api/v1/farms/{farm_id}/members`
  - `GET /api/v1/scans/history`
  - `GET /api/v1/scans/{id}`
- Khi API Tuần 4 chưa chạy, UI tự chuyển sang dữ liệu demo/localStorage để vẫn demo được luồng.

### Tuần 5 — OOD, Grad-CAM & Technician Proposal

- Kết quả Predict hiển thị `is_valid_leaf`, OOD score, cảnh báo ảnh không hợp lệ và gợi ý xử lý.
- Lịch sử chẩn đoán có trạng thái OOD và chi tiết khuyến nghị.
- Kỹ thuật viên xem top-3 và Grad-CAM từ `POST /api/v1/predict/explain`.
- Route `/app/proposals` cho Kỹ thuật viên gửi đề xuất bệnh qua `POST /api/v1/disease-proposals` và xem `/disease-proposals/mine`.

### Tuần 6 — Kết nối Admin

- Đề xuất của Kỹ thuật viên được thiết kế để Admin duyệt/từ chối trong ứng dụng `admin/`.
- Frontend xử lý đầy đủ loading, lỗi API và fallback demo cho các endpoint mới.

### Tuần 7 — Camera & Dashboard Farm

- Camera Capture dùng `<input capture="environment">` trên điện thoại.
- Route Manager `/app/farm-dashboard`, chọn từng Farm và gọi `GET /api/v1/stats/farm/{id}`.
- Dashboard có thống kê lượt quét, mẫu khỏe, mẫu cần chú ý, ảnh OOD, biểu đồ 7 ngày và phân bố kết quả.

Admin Panel đã được tách thành ứng dụng độc lập trong thư mục [`../admin`](../admin).

## Chạy dự án

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Mở `http://localhost:5173`. Guest có thể vào thẳng `http://localhost:5173/guest/scan`.

Biến môi trường mặc định:

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_ADMIN_URL=http://localhost:5174
```

## Tài khoản demo

Các tài khoản sau hoạt động ngay cả khi backend chưa chạy:

| Vai trò | Username | Password | Trang sau đăng nhập |
|---|---|---|---|
| Nông dân | `farmer` | `123456` | `/app/dashboard` |
| Kỹ thuật viên | `technician` | `123456` | `/app/dashboard` |
| Quản lý trang trại | `manager` | `123456` | `/app/dashboard` |
Đăng nhập bằng username khác sẽ gọi API backend thật.
Quản trị viên đăng nhập tại `http://localhost:5174/login`.

## Cấu trúc chính

```text
src/
├── api/                 # Axios client, predict, scans, managed users, farms...
├── components/
│   ├── auth/            # ProtectedRoute, RoleGuard
│   └── common/          # DataTable, CrudForm, Modal, StatCard...
├── contexts/            # AuthContext, PreferencesContext (VI/EN + theme)
├── data/                # Dữ liệu demo Tuần 1–7
├── layouts/             # AppLayout người dùng + GuestLayout
├── pages/
│   ├── public/          # Landing + Guest Scan
│   ├── auth/            # Login, Register
│   └── app/             # Dashboard, Scan, History, Farms, Managed Users...
├── styles/              # Tailwind entry CSS
└── utils/               # Role và localStorage helpers
```

## Build production

```bash
npm run build
npm run preview
```

Build đã được kiểm tra thành công với Vite 5.

> Lưu ý: các màn hình Tuần 4–7 dùng API-first nhưng tự fallback sang localStorage/dữ liệu demo cho đến khi Backend hoàn thiện toàn bộ router tương ứng.
