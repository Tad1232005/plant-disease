# BÁO CÁO ĐÁNH GIÁ RỦI RO HỆ THỐNG VÀ CÁC HẠNG MỤC TỒN ĐỌNG (BACKEND)

> **Dự án:** Hệ thống nhận diện bệnh lá cây (Plant Disease Identification & Farm Management)  
> **Thời gian cập nhật:** Tháng 10/2026  
> **Tài liệu tham chiếu:** `backend/app/services/predict_service.py`, `backend/app/api/v1/endpoints/`

---

## 1. TỔNG QUAN

Hệ thống Backend đã hoàn tất các chức năng cốt lõi:
- Xác thực người dùng (JWT + Refresh Token Cookie HttpOnly, phân quyền Role: `guest`, `user`, `manager`, `technician`, `admin`).
- Nhận diện bệnh lá cây đa tầng (**Two-Stage Cascading Inference với OOD Gating và Soft-Voting Ensemble**).
- Giải thích vùng bệnh với **Grad-CAM**.
- Quản lý trang trại (Farms), thành viên trang trại (Farm Members), đề xuất bệnh mới (Disease Proposals) và phiên bản mô hình (Model Versions).

Tuy nhiên, trong quá trình vận hành thực tế, demo hoặc khi đưa lên môi trường sản xuất (Production), hệ thống còn tồn tại các rủi ro kỹ thuật và hạng mục chưa triển khai cần được ghi nhận và có lộ trình xử lý.

---

## 2. DANH MỤC CÁC RỦI RO KỸ THUẬT VÀ VẬN HÀNH (CHƯA THỰC HIỆN)

### 🔴 RỦI RO 1: NGHẼN TẢI INFERENCE ĐỒNG THỜI (`MAX_CONCURRENT_INFERENCES = 1`)

* **Mức độ rủi ro:** Cao (khi demo nhiều người hoặc production)
* **Hiện trạng mã nguồn:**
  * File cấu hình: `MAX_CONCURRENT_INFERENCES=1`.
  * Trong `PredictService.predict_bounded`: sử dụng `BoundedSemaphore(MAX_CONCURRENT_INFERENCES)` không chặn (`blocking=False`).
* **Hệ quả / Rủi ro:**
  * Nếu có từ 2 người dùng gửi ảnh chẩn đoán trong cùng một thời điểm, request của người thứ hai sẽ lập tức bị từ chối với mã lỗi `HTTP 503 Service Unavailable: "Hệ thống đang bận xử lý chẩn đoán, vui lòng thử lại."`
* **Giải pháp đề xuất:**
  1. *Ngắn hạn:* Nâng cấu hình `.env` lên `MAX_CONCURRENT_INFERENCES=2` hoặc `3` tùy thuộc vào dung lượng RAM/VRAM của máy chủ.
  2. *Dài hạn:* Chuyển đổi cơ chế suy luận sang hàng đợi bất đồng bộ (**Asynchronous Task Queue** sử dụng Celery/Redis hoặc FastAPI BackgroundTasks), trả về `job_id` cho Client và thông báo kết quả qua WebSocket hoặc Polling.

---

### 🟠 RỦI RO 2: ẢNH CHỤP ĐIỆN THOẠI ĐỘ PHÂN GIẢI CAO VƯỢT QUÁ GIỚI HẠN PIXEL

* **Mức độ rủi ro:** Trung bình - Cao (người dùng dùng smartphone đời mới)
* **Hiện trạng mã nguồn:**
  * Giới hạn an toàn: `MAX_IMAGE_PIXELS = 20,000,000` (~20 Megapixels) và `MAX_UPLOAD_BYTES = 10,485,760` (10 MB).
* **Hệ quả / Rủi ro:**
  * Các smartphone hiện nay thường chụp ảnh độ phân giải 48MP, 64MP hoặc 108MP (dung lượng file raw có thể từ 12MB - 30MB). Khi người dùng chụp trực tiếp từ camera và gửi thẳng lên API, hệ thống sẽ ném lỗi `HTTP 413 Payload Too Large` hoặc `HTTP 422: Kích thước ảnh quá lớn`.
* **Giải pháp đề xuất:**
  1. *Phía Frontend:* Bổ sung bước tự động nén (compress) và resize ảnh trên trình duyệt thông qua HTML5 Canvas trước khi gửi FormData lên API (chuẩn hóa về cạnh tối đa 1920px hoặc 1080px).
  2. *Phía Backend:* Bổ sung xử lý stream downscaling ảnh an toàn trước khi nạp toàn bộ vào bộ nhớ PIL Image.

---

### 🟠 RỦI RO 3: CẤU HÌNH COOKIE REFRESH TOKEN KHI TRIỂN KHAI PRODUCTION (HTTPS & CORS)

* **Mức độ rủi ro:** Cao (khi triển khai môi trường máy chủ thật)
* **Hiện trạng mã nguồn:**
  * Môi trường Local: `COOKIE_SECURE=false`, `COOKIE_SAMESITE=lax`.
* **Hệ quả / Rủi ro:**
  * Khi deploy lên server có HTTPS và chia tách tên miền (ví dụ: Frontend tại `app.myfarm.vn` và Backend API tại `api.myfarm.vn`):
    * Trình duyệt sẽ **tự động chặn không gửi Refresh Token Cookie** vì vi phạm chính sách Cross-Site Cookie nếu không có cờ `Secure; SameSite=None`.
    * Dẫn đến người dùng không thể tự động gia hạn phiên đăng nhập (Silent Refresh bị lỗi 401).
* **Giải pháp đề xuất:**
  * Khi triển khai Production: Bắt buộc cấu hình trong biến môi trường:
    ```env
    COOKIE_SECURE=true
    COOKIE_SAMESITE=none
    PUBLIC_API_ORIGIN=https://api.myfarm.vn
    CORS_ORIGINS=["https://myfarm.vn","https://admin.myfarm.vn"]
    ```

---

### 🟡 RỦI RO 4: KHÓA TÀI NGUYÊN TÍNH TOÁN KHI TẠO ẢNH GRAD-CAM LIÊN TỤC

* **Mức độ rủi ro:** Trung bình
* **Hiện trạng mã nguồn:**
  * Trong `predict_service.py`: `_explain_lock = Lock()` và `_gradcam_capacity = BoundedSemaphore(MAX_CONCURRENT_GRADCAM)`.
  * Hàm tính Grad-CAM phải chạy backward pass trên mạng PyTorch để trích xuất gradient của feature map.
* **Hệ quả / Rủi ro:**
  * Quá trình backward pass tốn nhiều tài nguyên tính toán hơn forward pass thông thường. Nếu nhiều kỹ thuật viên/admin cùng bấm xem bản đồ nhiệt Grad-CAM, thời gian chờ của API sẽ tăng lên hoặc bị nghẽn lock.
* **Giải pháp đề xuất:**
  * Hiện tại hệ thống đã có cơ chế lưu đệm file kết quả (`scan.gradcam_path`). Tuy nhiên, cần bổ sung:
    * Rate limiting riêng cho endpoint `POST /scans/{id}/gradcam` (ví dụ: tối đa 5 lần/phút/tài khoản).
    * Giới hạn thời gian timeout cho tác vụ sinh Grad-CAM.

---

### 🟡 RỦI RO 5: QUẢN LÝ DUNG LƯỢNG LƯU TRỮ VÀ DỌN DẸP ẢNH CỤC BỘ (`storage/uploads`)

* **Mức độ rủi ro:** Trung bình (theo thời gian dài vận hành)
* **Hiện trạng mã nguồn:**
  * Toàn bộ ảnh scan của người dùng đăng nhập và ảnh Grad-CAM được lưu trực tiếp trên ổ đĩa server (`storage/uploads/`).
* **Hệ quả / Rủi ro:**
  * Sau một thời gian dài vận hành với hàng chục ngàn lượt quét, ổ cứng server có nguy cơ bị đầy dung lượng (Disk Full), gây treo cơ sở dữ liệu và sập tiến trình backend.
* **Giải pháp đề xuất:**
  1. *Ngắn hạn:* Viết script Cronjob định kỳ dọn dẹp các ảnh mồ côi (ảnh rác không gắn với `scan_id` nào trong DB) hoặc nén ảnh cũ.
  2. *Dài hạn:* Chuyển đổi storage từ lưu trữ file cục bộ sang Object Storage đám mây (Amazon S3, Cloudflare R2, hoặc MinIO tự host).

---

### 🟢 RỦI RO 6: SAO LƯU DỮ LIỆU ĐỊNH KỲ VÀ KHẮC PHỤC SỰ CỐ (DISASTER RECOVERY)

* **Mức độ rủi ro:** Thấp - Trung bình
* **Hiện trạng mã nguồn:**
  * Cơ sở dữ liệu PostgreSQL lưu trữ người dùng, nông trại, đề xuất và lịch sử quét.
  * Hiện chưa có cơ chế tự động backup snapshot ngoài script chạy thủ công.
* **Giải pháp đề xuất:**
  * Thiết lập lịch trình tự động `pg_dump` mỗi ngày vào 02:00 AM, nén file backup và đẩy lên dịch vụ lưu trữ an toàn tách biệt.

---

## 3. BẢNG TỔNG HỢP VÀ ĐỘ ƯU TIÊN XỬ LÝ (ACTION MATRIX)

| STT | Tên rủi ro / Hạng mục tồn đọng | Mức độ ảnh hưởng | Môi trường tác động | Độ ưu tiên | Hành động xử lý khuyến nghị |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **1** | **Nghẽn slot inference đồng thời** | Cao | Demo / Production | **P1 (Cao)** | Nâng `MAX_CONCURRENT_INFERENCES` lên 2-3 trong `.env` khi cấu hình máy cho phép. |
| **2** | **Ảnh camera điện thoại độ phân giải quá cao** | Trung bình | Người dùng di động | **P2 (Trung bình)** | Thêm bước canvas client-side resize ảnh trước khi upload. |
| **3** | **Cấu hình Cookie HTTPS / Cross-Site** | Cao | Production | **P1 (Cao)** | Chuyển `COOKIE_SECURE=true`, `SameSite=none` khi có chứng chỉ SSL và domain. |
| **4** | **Nghẽn tài nguyên do tính toán Grad-CAM** | Trung bình | Tính năng kỹ thuật | **P3 (Thấp)** | Áp dụng rate-limit riêng cho endpoint Grad-CAM. |
| **5** | **Đầy dung lượng ổ cứng lưu ảnh** | Trung bình | Vận hành dài hạn | **P3 (Thấp)** | Lên kế hoạch chuyển sang S3/R2 hoặc cronjob dọn rác. |
| **6** | **Tự động sao lưu Database** | Trung bình | Vận hành | **P2 (Trung bình)** | Cài đặt cronjob `pg_dump` tự động. |
