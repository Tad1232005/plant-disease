# Backend — FastAPI

API phục vụ model nhận diện bệnh lá cây. Endpoint chính: `POST /api/predict`
Nhận file ảnh, trả về `{ "label": "...", "confidence": 0.94 }`.

## 1. Setup môi trường
```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Copy model đã train
Từ thư mục `ml/models/`, copy 2 file sau vào `backend/app/models/`:
- `best_model.pt`
- `classes.json`

(Nếu chưa có model, backend sẽ báo lỗi `FileNotFoundError` rõ ràng khi khởi động — cứ liên hệ
bạn phụ trách ML để lấy 2 file này trước.)

## 3. Chạy server (dev)
```bash
uvicorn app.main:app --reload
```
Server chạy tại `http://localhost:8000`. Xem docs tự động (Swagger UI) tại
`http://localhost:8000/docs` — dùng luôn để test upload ảnh mà không cần Postman.

## 4. Test nhanh bằng curl
```bash
curl -X POST http://localhost:8000/api/predict \
  -F "file=@/path/to/leaf_image.jpg"
```

## 5. Chạy bằng Docker (tùy chọn, khi deploy)
```bash
docker build -t plant-disease-backend .
docker run -p 8000:8000 plant-disease-backend
```
