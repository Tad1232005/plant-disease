# Nhận diện bệnh lá cây (Plant Disease Detection)

Đồ án kết thúc học phần môn Quản lý phần mềm — Nhóm 3 người.
Phân loại một số nhóm bệnh phổ biến trên lá cây từ ảnh, kèm mức độ tin cậy (confidence score).

## Stack
- **ML**: Python, PyTorch (train + export `.pt`)
- **Backend**: Python, FastAPI (serve model qua REST API)
- **Frontend**: React (Vite)

## Cấu trúc thư mục
```
ml/          Data, notebook EDA, code train/evaluate model
backend/     FastAPI serve API /predict
frontend/    React app upload ảnh + hiển thị kết quả
docs/        Project charter, WBS, risk register, báo cáo
```

## Phân công nhánh (branching rule)
### Quy tắc đặt tên nhánh

- Bắt buộc đặt tên nhánh theo tên cá nhân (viết liền, không dấu, ngăn cách bằng dấu `-`).
- Ví dụ: `tad`.

### Workflow 5 bước chuẩn

1. **Trước khi code, luôn cập nhật `main` mới nhất:**

```bash
git checkout main
git pull origin main
```

2. **Tạo nhánh cá nhân theo đúng quy tắc tên:**

```bash
git checkout -b tad
```

3. **Code tính năng, sau đó add và commit rõ ràng:**

```bash
git add .
git commit -m "feat: mo ta ngan gon thay doi"
```

4. **Đẩy nhánh cá nhân lên GitHub:**

```bash
git push origin tad
```

5. **Tạo Pull Request (PR) để Leader review và merge vào `main`.**

### Lưu ý quan trọng

- Không bao giờ push trực tiếp lên `main`.
- Luôn kiểm tra và xử lý conflict trước khi merge PR.

## Setup nhanh từng phần
Xem README riêng trong mỗi thư mục:
- [`ml/README.md`](ml/README.md)
- [`backend/README.md`](backend/README.md)
- [`frontend/README.md`](frontend/README.md)
