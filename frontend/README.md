# Frontend — React (Vite)

Giao diện upload ảnh lá cây, gọi API backend, hiển thị nhãn bệnh + % độ tin cậy.

## 1. Setup
```bash
cd frontend
npm install
cp .env.example .env
```

## 2. Chạy dev server
```bash
npm run dev
```
Mở `http://localhost:5173`. Đảm bảo backend đang chạy ở `http://localhost:8000`
(xem `backend/README.md`), nếu không sẽ báo lỗi kết nối khi upload ảnh.

## 3. Build production
```bash
npm run build
```

## Cấu trúc
```
src/
├── App.jsx                     # layout chính
├── components/
│   ├── UploadImage.jsx         # kéo thả / chọn ảnh
│   └── ResultCard.jsx          # hiển thị nhãn + % confidence
└── api/predict.js              # gọi POST /api/predict
```
