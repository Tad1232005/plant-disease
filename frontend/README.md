# PlantCare AI Frontend — Tuần 1 & Tuần 2

Frontend React (Vite) cho hệ thống nhận diện bệnh lá cây, được nâng cấp từ code ban đầu của repo `Tad1232005/plant-disease`.

## Chức năng đã hoàn thành

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

### Tuần 2 — Component nền tảng & Admin

- `DataTable`: tìm kiếm, sắp xếp, phân trang, custom cell và action.
- `CrudForm`: tạo form từ cấu hình field, React Hook Form + Zod validation.
- Farm Management: CRUD giao diện, thống kê, tìm kiếm; lưu demo bằng localStorage.
- Disease Management: CRUD nội dung bệnh cho Admin.
- Thư viện bệnh cho người dùng thường.
- Admin Panel riêng: layout, sidebar, role guard và các route chờ Tuần 6.
- Service sẵn sàng nối API `/farms` và `/disease-info`.

## Chạy dự án

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Mở `http://localhost:5173`.

Biến môi trường mặc định:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

## Tài khoản demo

Các tài khoản sau hoạt động ngay cả khi backend chưa chạy:

| Vai trò | Username | Password | Trang sau đăng nhập |
|---|---|---|---|
| Nông dân | `farmer` | `123456` | `/app/dashboard` |
| Kỹ thuật viên | `technician` | `123456` | `/app/dashboard` |
| Quản lý trang trại | `manager` | `123456` | `/app/dashboard` |
| Quản trị viên | `admin` | `123456` | `/admin` |

Đăng nhập bằng username khác sẽ gọi API backend thật.

## Cấu trúc chính

```text
src/
├── api/                 # Axios client, auth, predict, farms, diseases
├── components/
│   ├── auth/            # ProtectedRoute, RoleGuard
│   └── common/          # DataTable, CrudForm, Modal, StatCard...
├── contexts/            # AuthContext
├── data/                # Dữ liệu demo Tuần 1–2
├── layouts/             # AppLayout, AdminLayout
├── pages/
│   ├── public/          # Landing
│   ├── auth/            # Login, Register
│   ├── app/             # Dashboard, Scan, History, Farms, Diseases
│   └── admin/           # Dashboard và các module quản trị
├── styles/              # Tailwind entry CSS
└── utils/               # Role và localStorage helpers
```

## Build production

```bash
npm run build
npm run preview
```

Build đã được kiểm tra thành công với Vite 5.

> Lưu ý: ở trạng thái repo hiện tại, backend đã có Auth và Predict. UI Farm/Disease dùng dữ liệu demo localStorage; khi backend hoàn thiện các router tương ứng, thay phần state trong hai page bằng `farmsApi` và `diseasesApi` đã chuẩn bị sẵn.
