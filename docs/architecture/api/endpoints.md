# Bảng endpoint REST (`/api/v1`)

Nguồn thật: `backend/app/api/v1/endpoints/`. Swagger: `http://127.0.0.1:8000/docs`.

## Auth — `auth.py` (prefix `/auth`)

| Method | Path | Quyền | Ghi chú |
|---|---|---|---|
| POST | `/auth/register` | public | Đăng ký |
| POST | `/auth/login` | public | Trả JWT access + refresh cookie |
| POST | `/auth/refresh` | cookie | Cấp lại access |
| POST | `/auth/logout` | user | Tăng `token_version` (thu hồi cả 2 token) |
| GET | `/auth/me` | user | Thông tin hiện tại |
| POST | `/auth/change-password` | user | Đổi mật khẩu (204) |

## Predict — `predict.py` (prefix `/predict`)

| Method | Path | Quyền | Ghi chú |
|---|---|---|---|
| GET | `/predict/capabilities` | optional | Mode, tier và danh sách model role được phép chọn (`allowed_model_types`) |
| POST | `/predict` | optional | `file` + `primary_model?` + `farm_id?`.<br>• **Guest**: Dừng ở Tầng 1 (EffNet-B0), MSP < 0.933487 => `is_valid_leaf=false` ("Không phải lá"), không lưu Scan.<br>• **Role đăng nhập**: Chọn model làm Primary (Tầng 1), bắt buộc chạy qua Tầng 2 để ensemble/cross-check, lưu Scan. FE ẩn chọn single/ensemble. |

## Scans — `scans.py` (prefix `/scans`)

| Method | Path | Ghi chú |
|---|---|---|
| GET | `/scans/history` | Lịch sử của chính user |
| GET | `/scans/{id}` | Chi tiết (chủ sở hữu) |
| DELETE | `/scans/{id}` | Xóa (204) |
| GET | `/scans/{id}/image` | File ảnh gốc |
| POST | `/scans/{id}/gradcam` | Sinh Grad-CAM giải thích |
| GET | `/scans/{id}/gradcam` | Xem Grad-CAM |

## Farms & Members — `farms.py`, `farm_members.py` (prefix `/farms`)

`GET/POST /farms`, `GET/PUT/DELETE /farms/{id}`, `POST/GET /farms/{id}/members`, `DELETE` member.
`GET /me/farms` — farm của chính user.

## Disease Info — `disease_info.py` (prefix `/disease-info`)

`GET` list + `GET /{label_key}` public; `POST/PUT/DELETE /{label_key}` admin.

## Proposals — `disease_proposals.py`

| Method | Path | Quyền |
|---|---|---|
| POST | `/disease-proposals` | technician (gửi đề xuất) |
| GET | `/disease-proposals/mine` | technician (đề xuất của mình) |
| GET | `/admin/disease-proposals` | admin (chờ duyệt) |
| PUT | `/admin/disease-proposals/{id}/approve` | admin |
| PUT | `/admin/disease-proposals/{id}/reject` | admin (`{review_note}`) |

## Users — `admin_users.py` (`/admin/users`), `manager_users.py` (`/manager/users`)

- Admin: `GET/POST /admin/users`, `GET /admin/users/{id}`, `PATCH /admin/users/{id}/status` (`{status, reason}`).
- Manager: `GET/POST /manager/users` (tạo Managed User role `user`), `GET/PATCH /manager/users/{id}(/status)`, `POST /{id}/reset-password`.

## Model Versions — `model_versions.py` (prefix `/admin/model-versions`)

`GET` list, `GET /{id}`, `POST` đăng ký từ `manifest.json`, `POST /{id}/activate`.

## Stats — `monitoring.py`

`GET /stats/farm/{id}`, `GET /stats/admin/overview`, `GET /stats/admin/recent-invalid`,
`GET /admin/scans`, `GET /admin/scans/{id}/image`. Health: `GET /health/live`, `/health/ready` — xem thêm [ood-contract](ood-contract.md) cho ngưỡng predict.

## Audit — `monitoring.py`

`GET /admin/audit-events` (admin, append-only): `?action=`, `?limit/offset`, mới nhất trước,
kèm `actor_name` (join users, fallback `#id`/`system`). Không có endpoint ghi — audit chỉ sinh từ business flow.
