# Nhận diện bệnh lá cây (Plant Disease Detection)

Đồ án kết thúc học phần môn Quản lý phần mềm — Nhóm 3 người.
Phân loại một số nhóm bệnh phổ biến trên lá cây từ ảnh, kèm mức độ tin cậy (confidence score).

## Stack
- **ML**: Python, PyTorch (train + export `.pt`, 38 lớp PlantVillage)
- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, JWT (`:8000`, Swagger `/docs`)
- **Frontend**: React 18, Vite 5, Tailwind, React Hook Form, Zod, Axios (`:5173`)
- **Admin**: React 18, app quản trị riêng (`:5174`)

## Cấu trúc thư mục
```
ml/          Data, notebook EDA, code train/evaluate model
backend/     FastAPI serve API /api/v1
frontend/    React app upload ảnh + hiển thị kết quả
admin/       React app quản trị riêng
docs/        Tài liệu kiến trúc + dự án (xem docs/README.md)
AGENTS.md    Quy ước dự án cho AI agent (single source of truth)
```

## Phân công nhánh (branching rule)
### Quy tắc đặt tên nhánh

- Nhánh tính năng: `feature/<ten-viet-lien-khong-dau>` (rẽ từ `dev`).
- Ví dụ: `feature/ood-threshold`.

### Workflow: feature → dev → main

1. **Trước khi code, luôn cập nhật `dev` mới nhất và rẽ nhánh từ đó:**

```bash
git checkout dev
git pull origin dev
git checkout -b feature/ten-tinh-nang
```

2. **Code tính năng, sau đó add và commit rõ ràng:**

```bash
git add .
git commit -m "feat: mo ta ngan gon thay doi"
```

3. **Đẩy nhánh và tạo Pull Request vào `dev`:**

```bash
git push origin feature/ten-tinh-nang
```

4. **Leader review và merge vào `dev`. Khi `dev` ổn định → tạo PR từ `dev` vào `main`.**

### Lưu ý quan trọng

- Không bao giờ push trực tiếp lên `dev` hay `main`.
- Luôn kiểm tra và xử lý conflict trước khi tạo PR.

## Setup nhanh từng phần
Xem README riêng trong mỗi thư mục:
- [`ml/README.md`](ml/README.md)
- [`backend/README.md`](backend/README.md)
- [`frontend/README.md`](frontend/README.md)
- [`admin/README.md`](admin/README.md)
