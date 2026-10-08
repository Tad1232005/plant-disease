# Vai trò và quyền hạn

| Đối tượng | Role | Đăng nhập | Tier tối đa | Model được phép chọn | Cơ chế suy luận | Chức năng chính |
|---|---|---|---|---|---|---|
| Khách | `guest` | Không | `basic` | Không (cố định `efficientnet_b0`) | **Chỉ Tầng 1** (MSP ≥ 0.933487, fail → "Không phải lá") | Quét thử tại `/guest/scan`, không lưu lịch sử, không gửi `farm_id` |
| Nông dân tự do | `user` (`created_by = null`) | Bắt buộc | `standard` (2 model) | `efficientnet_b0`, `mobilenet_v2` | **Cascade 2 Tầng** (Tầng 1 ổn → pass ngay; phân vân → Tầng 2 ensemble) | Scan cá nhân + lịch sử cá nhân, tra cứu bệnh (**không gọi API Farm**) |
| Nông dân thuộc trang trại | `user` (Managed, có `created_by`) | Bắt buộc | `standard` (2 model) | `efficientnet_b0`, `mobilenet_v2` | **Cascade 2 Tầng** (Tầng 1 ổn → pass ngay; phân vân → Tầng 2 ensemble) | Scan + gán vào farm được chỉ định (`/me/farms`), tra cứu bệnh |
| Kỹ thuật viên | `technician` | Bắt buộc | `advanced` (3 model) | `efficientnet_b0`, `mobilenet_v2`, `resnet50` | **Cascade 2 Tầng** (Tầng 1 ổn → pass ngay; phân vân → Tầng 2 ensemble) | Thêm Grad-CAM, top-3, gửi đề xuất bệnh (`/disease-proposals`) |
| Quản lý | `manager` | Bắt buộc | `standard` | `efficientnet_b0`, `mobilenet_v2` | **Cascade 2 Tầng** (Tầng 1 ổn → pass ngay; phân vân → Tầng 2 ensemble) | Tạo Managed User (role `user`), quản lý trang trại (`/farms`), dashboard `/stats/farm/{id}` |
| Quản trị | `admin` | Bắt buộc (app `:5174`) | `advanced` | `efficientnet_b0`, `mobilenet_v2`, `resnet50` | **Cascade 2 Tầng** (Tầng 1 ổn → pass ngay; phân vân → Tầng 2 ensemble) | Quản lý user/farm/disease/proposal/model-version, `stats/admin/overview` |

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

## Kế hoạch siết phân quyền (chưa code — đối chiếu Oct 2026)

Lỗ hổng hiện tại:
- `GET /farms` chỉ `manager` → trang Farms của admin chết (403).
- `GET /scans/history` chỉ trả scan của chính user → manager không xem được lịch sử quét của farmer do mình tạo (mới chỉ thấy số gộp qua `/stats/farm/{id}`).

Hướng sửa đã chốt (BE, không đụng FE):
1. `GET /farms` + `GET /farms/{id}` (+ xem members) mở thêm cho `admin`: admin thấy tất cả (thêm query `?owner_id=`), manager giữ farm mình. Thao tác ghi vẫn manager-only.
2. `GET /scans/history?user_id=`: xem hộ chỉ khi là manager và user đó do mình tạo (`created_by`), không thì 403. Admin đã có `/admin/scans?user_id=`.
3. Kèm test: admin list all farms; manager xem history của managed user; user lạ 403.
