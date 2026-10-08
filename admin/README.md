# PlantCare AI Admin

Ứng dụng React độc lập dành cho quản trị viên của hệ thống nhận diện bệnh lá cây.

## Chạy ứng dụng

```bash
cd admin
npm install
cp .env.example .env
npm run dev
```

Mở `http://localhost:5174`.

## Chức năng chính

- Duyệt/từ chối đề xuất bệnh của Kỹ thuật viên tại `/proposals`.
- Quản lý Farm tại `/farms` qua API `/farms` (list/create/update/delete).
- Quản lý Model Version tại `/models`: liệt kê bundle đã đăng ký, đăng ký bundle mới từ `manifest.json` và kích hoạt lên Production.
- Dashboard thống kê hệ thống từ `GET /api/v1/stats/admin/overview` tại `/system`.
- Nhật ký audit tại `/audit-logs`, hồ sơ cá nhân tại `/profile`.
- Mọi trang gọi API thật qua `src/services/` (không fallback demo).

Các API đã dùng:

- `GET /api/v1/admin/disease-proposals` + `PUT /api/v1/admin/disease-proposals/{id}/approve|reject`
- `GET /api/v1/admin/model-versions`, `GET /api/v1/admin/model-versions/{id}`, `POST /api/v1/admin/model-versions`, `POST /api/v1/admin/model-versions/{id}/activate`
- `GET /api/v1/stats/admin/overview`
- `GET /api/v1/admin/audit-events` (nhật ký kiểm toán, `?action=&limit=&offset=`)
- `GET/POST /api/v1/admin/users`, `PATCH /api/v1/admin/users/{id}/status`

## Cấu trúc

```text
admin/
├── src/
│   ├── components/     # Layout và UI dùng chung
│   ├── contexts/       # Phiên đăng nhập Admin
│   ├── pages/          # Dashboard và các trang quản trị
│   ├── routes/         # Bảo vệ route theo role admin
│   ├── services/       # Gọi FastAPI backend
│   ├── styles/
│   ├── App.jsx
│   └── main.jsx
├── public/
├── .env.example
└── package.json
```

Backend vẫn phải kiểm tra JWT và role `admin` trên mọi API quản trị; route guard phía React chỉ bảo vệ giao diện.
