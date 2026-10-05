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
- Quản lý Model Version tại `/models`: liệt kê bundle đã đăng ký, đăng ký bundle mới từ `manifest.json` và kích hoạt lên Production.
- Dashboard thống kê hệ thống từ `GET /api/v1/stats/admin/overview` tại `/system`.
- Các trang ưu tiên API thật (đề xuất, thống kê, người dùng, model version); trang Farm lưu dữ liệu cục bộ ở trình duyệt vì backend chưa có API farm cho Admin.

Các API đã chuẩn bị:

- `GET/PUT /api/v1/admin/disease-proposals`
- `GET/POST /api/v1/admin/model-versions`
- `POST /api/v1/admin/model-versions/{id}/activate`
- `GET /api/v1/stats/admin/overview`

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
