# Hướng Dẫn Kiểm Thử Backend API (Testing Guide)

Tài liệu hướng dẫn kiểm thử chi tiết cho toàn bộ các module backend của hệ thống **Plant Disease Detection**.

---

## 1. Authentication & Profile (Xác thực & Tài khoản)

> **Phân quyền:** Public, User, Manager, Technician, Admin
> **Prefix:** `/auth`

### 1.1 Đăng ký tài khoản người dùng mới

```http
POST /api/v1/auth/register
Content-Type: application/json
```

**Body:**
```json
{
  "username": "farmer_nam",
  "email": "farmer.nam@example.com",
  "password": "StrongPassword123!"
}
```

> ⚠️ Role luôn được gán mặc định là `user`. Nếu client gửi `role` khác sẽ bị từ chối `422`.

**Expected:** `201 Created`
```json
{
  "id": 10,
  "username": "farmer_nam",
  "email": "farmer.nam@example.com",
  "role": "user",
  "status": "active",
  "created_at": "2026-09-22T08:00:00Z",
  "created_by": null,
  "token_version": 1
}
```

**Case lỗi & Validation:**
| Case | Expected |
|---|---|
| `username` trùng lặp | `409 Conflict` |
| `email` trùng lặp | `409 Conflict` |
| `password` < 8 ký tự, thiếu chữ hoa/chữ số | `422 Unprocessable Entity` |
| Cố tình truyền thêm `role: "admin"` | `422 Unprocessable Entity` |

---

### 1.2 Đăng nhập hệ thống

```http
POST /api/v1/auth/login
Content-Type: application/json
```

**Body:**
```json
{
  "username": "farmer_nam",
  "password": "StrongPassword123!"
}
```

**Expected:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```
> Response đồng thời thiết lập **HttpOnly Cookie** `plant_disease_refresh` chứa Refresh Token (thời hạn 7 ngày).

**Case lỗi:**
| Case | Expected |
|---|---|
| Sai username hoặc mật khẩu | `401 Unauthorized` |
| Tài khoản đang bị khóa (`suspended`) | `401 Unauthorized` |
| Quá tần suất đăng nhập từ 1 IP | `429 Too Many Requests` (kèm `Retry-After`) |

---

### 1.3 Xem thông tin tài khoản hiện tại

```http
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

**Expected:** `200 OK` + `UserResponse`
```json
{
  "id": 10,
  "username": "farmer_nam",
  "email": "farmer.nam@example.com",
  "role": "user",
  "status": "active",
  "created_at": "2026-09-22T08:00:00Z",
  "created_by": null,
  "token_version": 1
}
```

**Case lỗi:**
- Không truyền token hoặc token hết hạn $\to$ `401 Unauthorized`
- Token version trong DB đã tăng (đã logout hoặc đổi mật khẩu) $\to$ `401 Unauthorized`

---

### 1.4 Làm mới Access Token (Refresh)

```http
POST /api/v1/auth/refresh
Cookie: plant_disease_refresh=<refresh_token>
```

**Expected:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### 1.5 Đổi mật khẩu

```http
POST /api/v1/auth/change-password
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Body:**
```json
{
  "current_password": "StrongPassword123!",
  "new_password": "NewStrongPassword456!"
}
```

**Expected:** `204 No Content`
> Mọi Access Token và Refresh Token cũ lập tức bị vô hiệu hóa (tăng `token_version`).

---

### 1.6 Đăng xuất

```http
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
```

**Expected:** `204 No Content` (Xóa HttpOnly Cookie và tăng `token_version`).

---

## 2. Predict & Inference (Chẩn đoán bệnh cây)

> **Phân quyền:** Guest (không đăng nhập) hoặc Authenticated (User / Manager / Technician / Admin)
> **Prefix:** `/predict`

### 2.1 Dự đoán bệnh qua ảnh lá cây

```http
POST /api/v1/predict
Authorization: Bearer <access_token> [tuỳ chọn]
Content-Type: multipart/form-data
```

**Form-data params:**
| Param | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `file` | Binary (image) | Có | File ảnh JPG/PNG/WEBP (tối đa 10MB) |
| `farm_id` | int | Không | Gắn kết quả quét với Farm (chỉ dành cho user hợp lệ) |
| `mode` | string | Không | `auto` (default), `basic`, `standard`, `advanced` |

> **Phân quyền mode tối đa theo vai trò:**
> - `Guest`: chỉ chạy `basic` (EfficientNet-B0) — **không lưu Scan DB/ảnh**.
> - `user`, `manager`: tối đa `standard` (Ensemble 2 model: EfficientNet + MobileNetV2).
> - `technician`, `admin`: tối đa `advanced` (Ensemble 3 model: EfficientNet + MobileNetV2 + ResNet50).

**Expected (Ảnh lá bệnh rõ ràng):** `200 OK`
```json
{
  "scan_id": 42,
  "label": "Tomato___Late_blight",
  "disease_name": "Mốc sương cà chua",
  "confidence": 0.945,
  "ensemble_mode": "standard",
  "is_rejected": false,
  "rejection_reason": null,
  "treatment": "Cắt tỉa lá bệnh, phun thuốc gốc đồng Mancozeb hoặc Ridomil Gold.",
  "top_k": [
    { "label": "Tomato___Late_blight", "disease_name": "Mốc sương cà chua", "confidence": 0.945 },
    { "label": "Tomato___Early_blight", "disease_name": "Đốm vòng cà chua", "confidence": 0.038 },
    { "label": "Tomato___healthy", "disease_name": "Cà chua khỏe mạnh", "confidence": 0.011 }
  ],
  "farm_assignment_status": "assigned"
}
```

**Expected (Ảnh ngoài phân phối / không phải lá cây):** `200 OK`
```json
{
  "scan_id": 43,
  "label": "unknown",
  "disease_name": "Không xác định",
  "confidence": 0.21,
  "ensemble_mode": "standard",
  "is_rejected": true,
  "rejection_reason": "low_confidence",
  "treatment": null,
  "top_k": [],
  "farm_assignment_status": "assigned"
}
```

**Case lỗi & Validation:**
| Case | Expected |
|---|---|
| Không gửi file / file rỗng | `422 Unprocessable Entity` |
| File không phải ảnh (PDF, EXE...) | `415 Unsupported Media Type` |
| Dung lượng file > 10MB | `413 Payload Too Large` |
| User thường cố gửi `mode=advanced` | `403 Forbidden` (vượt quyền) |
| Gán `farm_id` mà user không có quyền trong farm đó | `200 OK` kèm `farm_id: null` và `farm_assignment_status: "not_allowed"` |

---

### 2.2 Xem khả năng của Model (Capabilities)

```http
GET /api/v1/predict/capabilities
Authorization: Bearer <token> [tuỳ chọn]
```

**Expected:** `200 OK`
```json
{
  "available_modes": ["basic", "standard"],
  "default_mode": "standard",
  "active_models": [
    { "model_type": "efficientnet_b0", "version": "v1.0" },
    { "model_type": "mobilenet_v2", "version": "v1.0" }
  ]
}
```

---

## 3. Scans & Explainability (Lịch sử quét & Grad-CAM)

> **Phân quyền:** Owner-only (Người tạo scan mới có quyền xem/xóa scan của mình)
> **Prefix:** `/scans`

### 3.1 Danh sách lịch sử quét của cá nhân

```http
GET /api/v1/scans/history
Authorization: Bearer <user_token>
```

**Query params (tuỳ chọn):**
| Param | Kiểu | Mô tả |
|---|---|---|
| `limit` | int (1–100) | Số bản ghi (default: 50) |
| `offset` | int ≥ 0 | Vị trí bắt đầu (default: 0) |
| `farm_id` | int | Lọc theo Farm |

**Expected:** `200 OK`
```json
[
  {
    "id": 42,
    "user_id": 10,
    "farm_id": 1,
    "predicted_label": "Tomato___Late_blight",
    "confidence": 0.945,
    "is_rejected": false,
    "created_at": "2026-09-22T08:15:00Z"
  }
]
```

---

### 3.2 Chi tiết một lượt quét

```http
GET /api/v1/scans/{scan_id}
Authorization: Bearer <user_token>
```

**Expected:** `200 OK`
```json
{
  "id": 42,
  "user_id": 10,
  "farm_id": 1,
  "predicted_label": "Tomato___Late_blight",
  "confidence": 0.945,
  "is_rejected": false,
  "rejection_reason": null,
  "top_k": [
    { "rank": 1, "label": "Tomato___Late_blight", "confidence": 0.945 }
  ],
  "model_results": [
    { "model_type": "efficientnet_b0", "confidence": 0.952, "latency_ms": 32.5 },
    { "model_type": "mobilenet_v2", "confidence": 0.938, "latency_ms": 18.2 }
  ],
  "created_at": "2026-09-22T08:15:00Z"
}
```

**Case lỗi:**
- `scan_id` không tồn tại $\to$ `404 Not Found`
- User A cố truy cập `scan_id` của User B $\to$ `403 Forbidden`
- Admin truy cập qua endpoint này $\to$ `403 Forbidden` (Admin phải dùng `/admin/scans`)

---

### 3.3 Xem ảnh gốc đã quét

```http
GET /api/v1/scans/{scan_id}/image
Authorization: Bearer <user_token>
```

**Expected:** `200 OK` (Content-Type: `image/jpeg` hoặc `image/png`)

---

### 3.4 Tạo bản đồ nhiệt Grad-CAM (XAI)

```http
POST /api/v1/scans/{scan_id}/gradcam
Authorization: Bearer <technician_or_manager_or_admin_token>
```

> **Query/Body (tuỳ chọn):** `model_type` (`efficientnet_b0` | `mobilenet_v2` | `resnet50`).

**Expected:** `200 OK`
```json
{
  "scan_id": 42,
  "model_type": "efficientnet_b0",
  "gradcam_url": "/api/v1/scans/42/gradcam?model_type=efficientnet_b0",
  "target_layer": "features.8"
}
```

**Case lỗi:**
- Role `user` thường gọi endpoint này $\to$ `403 Forbidden`

---

### 3.5 Xem ảnh Grad-CAM

```http
GET /api/v1/scans/{scan_id}/gradcam?model_type=efficientnet_b0
Authorization: Bearer <technician_or_manager_or_admin_token>
```

**Expected:** `200 OK` (Content-Type: `image/jpeg` hoặc `image/png`)

---

### 3.6 Xoá lượt quét

```http
DELETE /api/v1/scans/{scan_id}
Authorization: Bearer <user_token>
```

**Expected:** `204 No Content`
> Xoá bản ghi Scan, TopK, Model results và dọn dẹp file ảnh trên ổ đĩa.

---

## 4. Farms Management (Quản lý Trang Trại)

> **Phân quyền:** Chỉ `manager` sở hữu trang trại
> **Prefix:** `/farms`

### 4.1 Danh sách trang trại của Manager

```http
GET /api/v1/farms
Authorization: Bearer <manager_token>
```

**Query params (tuỳ chọn):**
| Param | Kiểu | Mô tả |
|---|---|---|
| `limit` | int (1–100) | Số bản ghi (default: 50) |
| `offset` | int ≥ 0 | Phân trang (default: 0) |

**Expected:** `200 OK`
```json
[
  {
    "id": 1,
    "name": "Nông trại Đà Lạt Green",
    "owner_id": 3,
    "area_hectares": 5.5,
    "location_text": "Phường 7, TP. Đà Lạt, Lâm Đồng",
    "notes": "Chuyên canh cà chua và ớt chuông",
    "created_at": "2026-09-01T00:00:00Z",
    "archived_at": null
  }
]
```

---

### 4.2 Xem chi tiết trang trại

```http
GET /api/v1/farms/{farm_id}
Authorization: Bearer <manager_token>
```

**Expected:** `200 OK` + `FarmResponse`

**Case lỗi:**
- `farm_id` không tồn tại $\to$ `404 Not Found`
- `farm_id` thuộc về Manager khác $\to$ `403 Forbidden`
- Role `user` hoặc `admin` gọi $\to$ `403 Forbidden`

---

### 4.3 Tạo trang trại mới

```http
POST /api/v1/farms
Authorization: Bearer <manager_token>
Content-Type: application/json
```

**Body:**
```json
{
  "name": "Vườn mẫu Củ Chi",
  "area_hectares": 2.5,
  "location_text": "Củ Chi, TP. Hồ Chí Minh",
  "notes": "Thử nghiệm giống dưa leo mới"
}
```

**Expected:** `201 Created`
```json
{
  "id": 2,
  "name": "Vườn mẫu Củ Chi",
  "owner_id": 3,
  "area_hectares": 2.5,
  "location_text": "Củ Chi, TP. Hồ Chí Minh",
  "notes": "Thử nghiệm giống dưa leo mới",
  "created_at": "2026-09-22T08:30:00Z",
  "archived_at": null
}
```

**Validation cần test:**
| Case | Expected |
|---|---|
| `name` rỗng hoặc chỉ spaces | `422 Unprocessable Entity` |
| `area_hectares` $\le 0$ | `422 Unprocessable Entity` |
| Role `user` cố gọi tạo farm | `403 Forbidden` |

---

### 4.4 Cập nhật thông tin trang trại

```http
PUT /api/v1/farms/{farm_id}
Authorization: Bearer <manager_token>
Content-Type: application/json
```

**Body:**
```json
{
  "name": "Vườn mẫu Củ Chi (Mở rộng)",
  "area_hectares": 4.0,
  "location_text": "Củ Chi, TP. Hồ Chí Minh",
  "notes": "Đã mở rộng thêm khu B"
}
```

**Expected:** `200 OK` + `FarmResponse`

---

### 4.5 Lưu trữ / Vô hiệu hóa trang trại (Soft Delete)

```http
DELETE /api/v1/farms/{farm_id}
Authorization: Bearer <manager_token>
```

> ⚠️ Là **soft delete**: thiết lập `archived_at = CURRENT_TIMESTAMP`, giữ nguyên lịch sử quét liên quan đến farm.

**Expected:** `204 No Content`

---

### 4.6 Danh sách trang trại của tôi (Dành cho Member & Manager)

```http
GET /api/v1/me/farms
Authorization: Bearer <token>
```

> **Logic:**
> - Nếu là `manager`: trả về danh sách farm do chính Manager sở hữu.
> - Nếu là `user` được quản lý: trả về danh sách farm mà user đã được add làm Member.
> - Nếu là user tự do: trả về mảng rỗng `[]`.

**Expected:** `200 OK` (list các FarmResponse)

---

## 5. Farm Members (Thành viên Trang Trại)

> **Phân quyền:** Chỉ `manager` sở hữu trang trại
> **Prefix:** `/farms/{farm_id}/members`

### 5.1 Lấy danh sách thành viên trong farm

```http
GET /api/v1/farms/{farm_id}/members
Authorization: Bearer <manager_token>
```

**Expected:** `200 OK`
```json
[
  {
    "farm_id": 1,
    "user_id": 10,
    "added_by": 3,
    "created_at": "2026-09-05T00:00:00Z"
  }
]
```

---

### 5.2 Thêm thành viên vào farm

```http
POST /api/v1/farms/{farm_id}/members
Authorization: Bearer <manager_token>
Content-Type: application/json
```

**Body:**
```json
{
  "user_id": 11
}
```

**Expected:** `201 Created`
```json
{
  "farm_id": 1,
  "user_id": 11,
  "added_by": 3,
  "created_at": "2026-09-22T08:35:00Z"
}
```

**Case lỗi:**
| Case | Expected |
|---|---|
| User không do chính Manager này tạo ra | `403 Forbidden` |
| User đã là thành viên của farm này | `409 Conflict` |
| `farm_id` hoặc `user_id` không tồn tại | `404 Not Found` |

---

### 5.3 Xoá thành viên khỏi farm

```http
DELETE /api/v1/farms/{farm_id}/members/{user_id}
Authorization: Bearer <manager_token>
```

**Expected:** `204 No Content`

---

## 6. Disease Info (Từ Điển Bệnh Cây Trồng)

> **Phân quyền:**
> - Đọc (`GET`): Public (không cần login)
> - Ghi (`POST`, `PUT`, `DELETE`): Chỉ `admin`
> **Prefix:** `/disease-info`

### 6.1 Lấy danh sách bệnh cây trồng

```http
GET /api/v1/disease-info
```

**Query params (tuỳ chọn):**
| Param | Kiểu | Mô tả |
|---|---|---|
| `limit` | int (1–100) | Số bản ghi (default: 50) |
| `offset` | int ≥ 0 | Phân trang (default: 0) |

**Expected:** `200 OK`
```json
[
  {
    "id": 1,
    "label_key": "Tomato___Early_blight",
    "disease_name": "Bệnh đốm vòng cà chua",
    "description": "Vết đốm màu nâu đen hình tròn đồng tâm trên lá già.",
    "treatment": "Cắt tỉa lá bệnh, phun thuốc gốc đồng.",
    "severity_level": "medium",
    "content_version": 1,
    "is_active": true,
    "created_at": "2026-09-01T00:00:00Z",
    "updated_at": "2026-09-01T00:00:00Z"
  }
]
```

---

### 6.2 Xem chi tiết bệnh theo label_key

```http
GET /api/v1/disease-info/Tomato___Early_blight
```

**Expected:** `200 OK` + `DiseaseInfoResponse`

**Case lỗi:**
- `label_key` không tồn tại hoặc đã bị ẩn $\to$ `404 Not Found`

---

### 6.3 Tạo mới thông tin bệnh

```http
POST /api/v1/disease-info
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**Body:**
```json
{
  "label_key": "Corn___Common_rust",
  "disease_name": "Bệnh gỉ sắt ngô",
  "description": "Các ổ mụn mủ nhỏ màu nâu đỏ rải rác trên cả hai mặt lá.",
  "treatment": "Sử dụng giống kháng, phun thuốc trừ nấm phổ rộng khi phát hiện sớm.",
  "severity_level": "medium"
}
```

**Expected:** `201 Created`

**Case lỗi:**
- Trùng `label_key` $\to$ `409 Conflict`
- User thường hoặc Manager gọi $\to$ `403 Forbidden`

---

### 6.4 Cập nhật thông tin bệnh

```http
PUT /api/v1/disease-info/{label_key}
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**Body:**
```json
{
  "disease_name": "Bệnh gỉ sắt ngô (Cập nhật)",
  "description": "Mô tả chi tiết bổ sung...",
  "treatment": "Cắt tỉa và phun Mancozeb.",
  "severity_level": "high"
}
```

**Expected:** `200 OK` (Trường `content_version` tự động tăng lên 1 đơn vị).

---

### 6.5 Ẩn thông tin bệnh (Soft Delete)

```http
DELETE /api/v1/disease-info/{label_key}
Authorization: Bearer <admin_token>
```

> ⚠️ Đặt `is_active = false` để ẩn khỏi danh mục public nhưng vẫn bảo tồn liên kết trong các Scan lịch sử.

**Expected:** `204 No Content`

---

## 7. Disease Proposals (Đề Xuất & Duyệt Nội Dung Bệnh)

> **Phân quyền:**
> - Gửi đề xuất: Chỉ `technician`
> - Xem và duyệt: Chỉ `admin`
> **Prefix:** `/disease-proposals`, `/admin/disease-proposals`

### 7.1 Kỹ thuật viên gửi đề xuất sửa đổi bệnh

```http
POST /api/v1/disease-proposals
Authorization: Bearer <technician_token>
Content-Type: application/json
```

**Body:**
```json
{
  "label_key": "Tomato___Early_blight",
  "disease_name": "Bệnh đốm vòng cà chua (Đề xuất)",
  "description": "Bổ sung dấu hiệu vết bệnh ban đầu viền vàng.",
  "treatment": "Phun luân phiên gốc đồng và Chlorothalonil.",
  "severity_level": "high",
  "base_content_version": 1
}
```

**Expected:** `201 Created`
```json
{
  "id": 5,
  "label_key": "Tomato___Early_blight",
  "disease_name": "Bệnh đốm vòng cà chua (Đề xuất)",
  "proposal_type": "update_content",
  "status": "pending",
  "proposer_id": 4,
  "reviewer_id": null,
  "review_note": null,
  "created_at": "2026-09-22T08:40:00Z",
  "reviewed_at": null
}
```

**Case lỗi:**
| Case | Expected |
|---|---|
| `base_content_version` khác với version hiện tại trong DB | `409 Conflict` (Nội dung đã bị sửa đổi, cần refresh) |
| `label_key` không tồn tại trong từ điển | `404 Not Found` |
| Non-technician cố submit | `403 Forbidden` |

---

### 7.2 Kỹ thuật viên xem các đề xuất của mình

```http
GET /api/v1/disease-proposals/mine
Authorization: Bearer <technician_token>
```

**Query params (tuỳ chọn):**
| Param | Kiểu | Mô tả |
|---|---|---|
| `status` | string | `pending`, `approved`, `rejected` |
| `limit` | int (1–100) | Số bản ghi (default: 50) |
| `offset` | int ≥ 0 | Phân trang (default: 0) |

**Expected:** `200 OK` (list các ProposalResponse)

---

### 7.3 Admin xem danh sách đề xuất toàn hệ thống

```http
GET /api/v1/admin/disease-proposals
Authorization: Bearer <admin_token>
```

**Query params (tuỳ chọn):**
| Param | Kiểu | Mô tả |
|---|---|---|
| `status` | string | Lọc trạng thái |
| `label_key` | string | Lọc theo nhãn bệnh |
| `proposer_id` | int | Lọc theo kỹ thuật viên |
| `limit` | int (1–100) | Số bản ghi |
| `offset` | int ≥ 0 | Phân trang |

**Expected:** `200 OK`

---

### 7.4 Admin phê duyệt đề xuất

```http
PUT /api/v1/admin/disease-proposals/{proposal_id}/approve
Authorization: Bearer <admin_token>
```

**Expected:** `200 OK`
```json
{
  "id": 5,
  "status": "approved",
  "reviewer_id": 1,
  "reviewed_at": "2026-09-22T08:45:00Z"
}
```
> Đồng thời tự động cập nhật nội dung vào bảng `disease_info` và tăng `content_version`.

**Case lỗi:**
- Đề xuất đã bị `rejected` trước đó $\to$ `409 Conflict`

---

### 7.5 Admin từ chối đề xuất (kèm lý do)

```http
PUT /api/v1/admin/disease-proposals/{proposal_id}/reject
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**Body:**
```json
{
  "review_note": "Gợi ý thuốc chưa được Bộ NN&PTNT cấp phép cho cây trồng này."
}
```

**Expected:** `200 OK` (Trạng thái chuyển thành `rejected`).

**Case lỗi:**
| Case | Expected |
|---|---|
| `review_note` rỗng hoặc thiếu | `422 Unprocessable Entity` |
| Đề xuất đã được duyệt trước đó | `409 Conflict` |

---

## 8. User Management (Quản Lý Người Dùng)

> **Phân quyền:**
> - `/admin/users`: Chỉ `admin`
> - `/manager/users`: Chỉ `manager`

### 8.1 Admin tạo Technician hoặc Manager

```http
POST /api/v1/admin/users
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**Body:**
```json
{
  "username": "tech_lan",
  "email": "lan.tech@example.com",
  "password": "StrongPassword123!",
  "role": "technician"
}
```

> **Lưu ý:** Admin chỉ được tạo `technician` hoặc `manager`. Không tạo `admin` khác.

**Expected:** `201 Created` + `UserResponse`

---

### 8.2 Admin lấy danh sách tài khoản toàn hệ thống

```http
GET /api/v1/admin/users
Authorization: Bearer <admin_token>
```

**Query params (tuỳ chọn):**
| Param | Kiểu | Mô tả |
|---|---|---|
| `role` | string | `user`, `technician`, `manager`, `admin` |
| `limit` | int (1–100) | Số bản ghi |
| `offset` | int ≥ 0 | Phân trang |

**Expected:** `200 OK`

---

### 8.3 Admin xem chi tiết bất kỳ người dùng nào

```http
GET /api/v1/admin/users/{user_id}
Authorization: Bearer <admin_token>
```

**Expected:** `200 OK` + `UserResponse`

---

### 8.4 Admin khóa hoặc mở khóa tài khoản (Suspend / Activate)

```http
PATCH /api/v1/admin/users/{user_id}/status
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**Body (Khóa tài khoản):**
```json
{
  "status": "suspended",
  "reason": "Phát hiện dấu hiệu tấn công upload abuse"
}
```

**Expected:** `200 OK`
```json
{
  "id": 10,
  "username": "farmer_nam",
  "status": "suspended",
  "token_version": 2
}
```
> Khi khóa tài khoản, `token_version` tăng ngay lập tức $\to$ mọi phiên đăng nhập của user này bị vô hiệu hóa tức thì.

**Body (Mở khóa tài khoản):**
```json
{
  "status": "active",
  "reason": "Đã xác minh và hoàn tất kiểm tra an toàn"
}
```

---

### 8.5 Manager tạo tài khoản người dùng nông dân (Managed User)

```http
POST /api/v1/manager/users
Authorization: Bearer <manager_token>
Content-Type: application/json
```

**Body:**
```json
{
  "username": "worker_tam",
  "email": "tam.worker@example.com",
  "password": "StrongPassword123!"
}
```

> ⚠️ Role luôn được hardcode là `user` và `created_by = manager_id`. Nếu gửi trường `role` sẽ nhận `422`.

**Expected:** `201 Created`

---

### 8.6 Manager xem danh sách tài khoản do mình tạo

```http
GET /api/v1/manager/users
Authorization: Bearer <manager_token>
```

**Expected:** `200 OK` (Chỉ hiển thị các User có `created_by == manager.id`).

---

### 8.7 Manager xem chi tiết tài khoản do mình tạo

```http
GET /api/v1/manager/users/{user_id}
Authorization: Bearer <manager_token>
```

**Expected:** `200 OK` + `UserResponse`

**Case lỗi:**
- `user_id` do Manager khác tạo $\to$ `404 Not Found` (cô lập dữ liệu).

---

## 9. Model Versions (Quản Lý Phiên Bản Mô Hình AI)

> **Phân quyền:** Chỉ `admin`
> **Prefix:** `/admin/model-versions`

### 9.1 Xem danh sách phiên bản mô hình

```http
GET /api/v1/admin/model-versions
Authorization: Bearer <admin_token>
```

**Query params (tuỳ chọn):**
| Param | Kiểu | Mô tả |
|---|---|---|
| `model_type` | string | `efficientnet_b0`, `mobilenet_v2`, `resnet50` |
| `is_active` | bool | `true` (đang chạy), `false` (staging/archive) |
| `limit` | int (1–100) | Số bản ghi |
| `offset` | int ≥ 0 | Phân trang |

**Expected:** `200 OK`
```json
[
  {
    "id": 1,
    "version_name": "efficientnet_b0_v1",
    "model_type": "efficientnet_b0",
    "is_active": true,
    "is_enabled": true,
    "temperature": 1.4939,
    "accuracy": 0.985,
    "macro_f1": 0.982,
    "created_at": "2026-09-01T00:00:00Z"
  }
]
```

---

### 9.2 Xem chi tiết một phiên bản mô hình

```http
GET /api/v1/admin/model-versions/{version_id}
Authorization: Bearer <admin_token>
```

**Expected:** `200 OK` + `ModelVersionResponse` (kèm đường dẫn `file_path`, `sha256`, `temperature_path`...).

---

### 9.3 Đăng ký phiên bản mô hình mới từ manifest.json

```http
POST /api/v1/admin/model-versions
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**Body:**
```json
{
  "manifest_path": "C:/Project/plant-disease/ml/models/bundle_v2/manifest.json",
  "accuracy": 0.988,
  "macro_f1": 0.986
}
```

> Manifest file phải chứa đường dẫn file trọng số `.pt`, `classes.json`, `temperature` và mã băm `sha256`.
> Version mới sau khi đăng ký sẽ ở trạng thái `is_active = false`.

**Expected:** `201 Created`

**Case lỗi:**
| Case | Expected |
|---|---|
| Đường dẫn tương đối (không phải tuyệt đối) | `422 Unprocessable Entity` |
| Manifest file không tồn tại hoặc sai định dạng | `422 Unprocessable Entity` |
| File `.pt` không load được hoặc số output không khớp classes | `422 Unprocessable Entity` |

---

### 9.4 Kích hoạt đưa mô hình lên Production (Hot Activation)

```http
POST /api/v1/admin/model-versions/{version_id}/activate
Authorization: Bearer <admin_token>
```

> **Quy trình kích hoạt:**
> 1. Load strict state dict & validate.
> 2. Warm-up forward pass thử 1 tensor ngẫu nhiên.
> 3. Kích hoạt version mới và hủy kích hoạt version cũ cùng `model_type` trong cùng 1 transaction.
> 4. Rollback toàn bộ nếu warm-up thất bại.

**Expected:** `200 OK`
```json
{
  "id": 4,
  "version_name": "efficientnet_b0_v2",
  "model_type": "efficientnet_b0",
  "is_active": true,
  "deactivated_version_id": 1,
  "deactivated_version_name": "efficientnet_b0_v1",
  "warmup_latency_ms": 45.2
}
```

---

## 10. Monitoring & System Statistics (Thống Kê & Giám Sát)

> **Phân quyền:**
> - `/stats/farm/{farm_id}`: Chỉ `manager` sở hữu trang trại
> - `/stats/admin/*` và `/admin/scans`: Chỉ `admin`

### 10.1 Thống kê trang trại (Dành cho Manager)

```http
GET /api/v1/stats/farm/{farm_id}
Authorization: Bearer <manager_token>
```

**Expected:** `200 OK`
```json
{
  "farm_id": 1,
  "total_scans": 150,
  "healthy_scans": 95,
  "diseased_scans": 50,
  "rejected_scans": 5,
  "top_diseases": [
    { "disease_name": "Mốc sương cà chua", "count": 28 },
    { "disease_name": "Đốm vòng cà chua", "count": 14 }
  ]
}
```

---

### 10.2 Tổng quan hệ thống (Dành cho Admin)

```http
GET /api/v1/stats/admin/overview
Authorization: Bearer <admin_token>
```

**Expected:** `200 OK`
```json
{
  "total_users": 48,
  "total_farms": 12,
  "total_scans": 1250,
  "rejected_scans": 42,
  "users_by_role": {
    "admin": 2,
    "technician": 5,
    "manager": 10,
    "user": 31
  },
  "scans_by_day": [120, 145, 160, 130, 190, 210, 175]
}
```

---

### 10.3 Giám sát các lượt quét bất thường / bị từ chối

```http
GET /api/v1/stats/admin/recent-invalid
Authorization: Bearer <admin_token>
```

**Expected:** `200 OK` (Danh sách các lượt quét gần nhất bị gắn cờ `is_rejected=true`).

---

### 10.4 Admin giám sát danh sách lượt quét toàn hệ thống

```http
GET /api/v1/admin/scans
Authorization: Bearer <admin_token>
```

**Query params (tuỳ chọn):**
| Param | Kiểu | Mô tả |
|---|---|---|
| `user_id` | int | Lọc theo người dùng |
| `farm_id` | int | Lọc theo nông trại |
| `is_rejected` | bool | Lọc lượt quét bị từ chối |
| `limit` | int (1–100) | Số bản ghi |
| `offset` | int ≥ 0 | Phân trang |

**Expected:** `200 OK`

---

### 10.5 Admin xem ảnh quét phục vụ giám sát

```http
GET /api/v1/admin/scans/{scan_id}/image
Authorization: Bearer <admin_token>
```

**Expected:** `200 OK` (image/jpeg hoặc image/png)
