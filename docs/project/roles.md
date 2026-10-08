# Vai trò và quyền hạn

| Đối tượng | Role | Đăng nhập | Tier tối đa | Model được phép chọn | Cơ chế suy luận | Chức năng chính |
|---|---|---|---|---|---|---|
| Khách | `guest` | Không | `basic` | Không (cố định `efficientnet_b0`) | **Chỉ Tầng 1** (MSP ≥ 0.933487, fail → "Không phải lá") | Quét thử tại `/guest/scan`, không lưu lịch sử, không gửi `farm_id` |
| Nông dân | `user` | Bắt buộc | `standard` (2 model) | `efficientnet_b0`, `mobilenet_v2` | **Bắt buộc 2 Tầng** (Primary + Aux -> Ensemble) | Scan + lịch sử + farm của mình, tra cứu bệnh |
| Kỹ thuật viên | `technician` | Bắt buộc | `advanced` (3 model) | `efficientnet_b0`, `mobilenet_v2`, `resnet50` | **Bắt buộc 2 Tầng** (Primary + Aux -> Ensemble) | Thêm Grad-CAM, top-3, gửi đề xuất bệnh (`/disease-proposals`) |
| Quản lý | `manager` | Bắt buộc | `standard` | `efficientnet_b0`, `mobilenet_v2` | **Bắt buộc 2 Tầng** (Primary + Aux -> Ensemble) | Tạo Managed User (role `user`), gán vào farm, dashboard `/stats/farm/{id}` |
| Quản trị | `admin` | Bắt buộc (app `:5174`) | `advanced` | `efficientnet_b0`, `mobilenet_v2`, `resnet50` | **Bắt buộc 2 Tầng** (Primary + Aux -> Ensemble) | Quản lý user/farm/disease/proposal/model-version, `stats/admin/overview` |

## Ma trận tạo tài khoản

| Người tạo | Được tạo | Endpoint |
|---|---|---|
| Public (tự đăng ký) | `user` | `POST /auth/register` |
| Admin | `technician`, `manager` | `POST /admin/users` |
| Manager | Managed User (`user`, có `created_by`) | `POST /manager/users` |

- Khóa/mở tài khoản bắt buộc có `reason`: Admin `PATCH /admin/users/{id}/status`,
  Manager `PATCH /manager/users/{id}/status`. Không tự khóa chính mình (FE chặn).
- JWT lưu ở client (`utils/storage.js`); route guard: `ProtectedRoute`/`RoleGuard` (frontend),
  `AdminRoute` (admin). Mọi quyền thật do BE kiểm tra (`require_role`).

## Chức năng mở rộng theo đối tượng

- Gợi ý xử lý/điều trị: Nông dân (chính), Kỹ thuật viên, Quản lý.
- Grad-CAM + top-3: Kỹ thuật viên.
- Dashboard theo farm: Quản lý. Thống kê toàn hệ thống + quản trị: Admin.
- Cảnh báo ảnh không hợp lệ / không phải lá (`is_valid_leaf=false`): Áp dụng cho cả Khách (Guest) ngay tại Tầng 1 và mọi role đã đăng nhập (sau khi qua 2 tầng).
