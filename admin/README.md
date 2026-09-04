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

Tài khoản demo: `admin` / `123456`.

## Chức năng Tuần 6–7

- Duyệt/từ chối đề xuất bệnh của Kỹ thuật viên tại `/proposals`.
- Quản lý Model Version, accuracy, calibration và model Production tại `/models`.
- Dashboard thống kê hệ thống từ `GET /api/v1/stats/admin/overview` tại `/system`.
- Các trang ưu tiên API thật và tự dùng dữ liệu demo nếu Backend chưa có endpoint.

Các API đã chuẩn bị:

- `GET/PUT /api/v1/admin/disease-proposals`
- `GET/POST/PUT /api/v1/model-versions`
- `GET /api/v1/stats/admin/overview`

## Cấu trúc

```text
admin/
├── src/
│   ├── components/     # Layout và UI dùng chung
│   ├── contexts/       # Phiên đăng nhập Admin
│   ├── data/           # Dữ liệu demo
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
