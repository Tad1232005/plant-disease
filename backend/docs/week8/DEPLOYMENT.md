# Backend: checklist triển khai và nghiệm thu không ML

> Cập nhật rc.2: schema head hiện tại là `d0e1f2a3b4c5`, có thêm bảng vận hành
> `auth_rate_limits`. Đọc [bổ sung không ML](NON_ML_COMPLETION.md) trước khi thao tác;
> các số liệu c9 bên dưới là mốc triển khai đã kiểm chứng trước rc.2.

Ngày 16/09/2026. Chỉ backend. Dùng cùng file `.env` hiện có; không tạo
`postgres.env`, không đưa mật khẩu thật vào Git. Cấu hình mẫu trong `.env.example`.
Mốc rc.1 cần `c9d0e1f2a3b4`; code rc.2 hiện cần `d0e1f2a3b4c5`.
Các số liệu kiểm thử bên dưới thuộc rc.1, trừ khi ghi rõ khác.

## 1. Kiểm tra trước khi thao tác

Từ thư mục `backend`, trong virtual environment:

```powershell
python -m scripts.preflight --config-only
python -m scripts.preflight
```

Exit code 0 = các kiểm tra trong scope đạt, 1 = có lỗi. Warning không làm fail.
JSON không in database URL, mật khẩu, JWT secret hoặc nội dung người dùng.
Lệnh chỉ đọc, timeout truy vấn/kết nối; không tự migrate, tạo tài khoản, tạo thư
mục hay load trọng số. Schema check phát hiện revision, bảng/cột thiếu; không
thay thế `alembic check` đối chiếu toàn bộ type/index/constraint.
Kiểm tra quyền thư mục là sơ bộ qua hệ điều hành, không ghi file thử.

Kết quả đọc DB ứng dụng ngày 16/09: còn ở `b8c9d0e1f2a3`, thiếu
`audit_events`, `disease_proposals`, `users.status`, `disease_info.content_version`.
Không chạy API nghiệp vụ mới trước khi nâng schema.

## 2. Nâng DB đã có dữ liệu (người vận hành chủ động thực hiện)

1. Xác nhận `.env` đúng DB. Dừng toàn bộ API worker/job ghi dữ liệu và chờ request
   đang chạy kết thúc; PostgreSQL vẫn hoạt động.
2. Tạo backup DB + ảnh bằng công cụ tuần 7. Chọn output mới, chưa tồn tại:

```powershell
python -m scripts.backup_restore --pg-bin "C:\Program Files\PostgreSQL\18\bin" backup --output backups\before-c9-20260916 --writers-stopped
```

3. Phải có manifest hoàn chỉnh và kiểm chứng restore vào DB mới trước khi nâng
   dữ liệu quan trọng. Không tự xóa ảnh thiếu hoặc bỏ qua lỗi để ép backup chạy.
4. Nâng schema trong maintenance window:

```powershell
alembic current
alembic upgrade head
alembic current
python -m scripts.preflight
```

5. Chỉ bật lại API sau khi revision/structure đạt. Test login, Farm, members,
   proposal, stats bằng tài khoản kiểm thử đã thống nhất. Không dùng downgrade
   như rollback dữ liệu: downgrade c9 làm mất bảng proposal/audit. Nếu cần phục hồi,
   restore vào DB mới và chuyển cấu hình sau xác nhận riêng của người vận hành.

Hướng dẫn backup/restore chi tiết và giới hạn: [tuần 7](../week7/REPORT.md).
DB và uploads phải khớp cùng snapshot vận hành; model bundle cần sao lưu riêng.

## 3. Tạo Admin đầu tiên, không phụ thuộc ML

Chỉ trên DB đã migrate và chưa có bất kỳ Admin nào:

```powershell
python -m scripts.bootstrap_admin --username owner_admin --confirm-create
```

Nhập mật khẩu hai lần tại prompt ẩn. Không có tham số `--password`, không đọc
mật khẩu từ biến môi trường và không hỗ trợ pipe. Có thể thêm `--email` và
`--full-name`. Validation giống đăng ký (tối thiểu 8 ký tự, chữ hoa/thường/số);
người vận hành nên dùng mật khẩu dài, riêng biệt.

Lệnh tạo đúng một Admin + audit trong cùng transaction, có lock chống hai lệnh
bootstrap đồng thời. Nếu Admin đã tồn tại (kể cả bị suspended), username/email
trùng hoặc audit lỗi thì từ chối; không đổi mật khẩu, nâng role hay mở khóa tài
khoản cũ. Đây là CLI cho người có quyền DB, không phải API đăng ký Admin.
Lệnh không tạo disease/model/demo users. Public disease list có thể rỗng cho
đến khi Admin nhập nội dung. `seed_week2` chỉ dành cho dev/demo, production bị chặn.

## 4. Các biến cần chốt trước production

| Biến | Yêu cầu |
| --- | --- |
| APP_ENV | `production` để bật guard; mặc định development không chứng nhận an toàn production |
| SECRET_KEY | Sinh ngẫu nhiên ít nhất 32 byte, khác mỗi môi trường; không dùng placeholder |
| POSTGRES_* / DATABASE_URL | Credential riêng; URL override phải dùng `postgresql+psycopg://` |
| COOKIE_SECURE | `true` |
| COOKIE_SAMESITE | `lax`/`strict` nếu cùng site; `none` khi thật sự cần cross-site, bắt buộc Secure |
| CORS_ORIGINS | JSON array origin FE HTTPS chính xác, không wildcard/path/trailing slash |
| PUBLIC_API_ORIGIN | Origin API HTTPS bên ngoài, không path/trailing slash; cho phép Swagger Auth |
| UPLOAD_DIR | Kho riêng tư, writable với đúng user chạy API, có backup |
| MODEL_ARTIFACT_ROOT | Bundle riêng read-only; không đưa weights vào Docker image |

Giới hạn inference/upload/pool và TTL phải là giá trị dương (DB_MAX_OVERFLOW
cho phép 0). Không đánh giá chất lượng ML hoặc đổi threshold trong đợt này.

Runtime DB role production không được là superuser/CREATEDB/CREATEROLE/BYPASSRLS:
preflight production báo fail nếu phát hiện. Tách role chạy migration khỏi role
API, cấp quyền schema/table/sequence thích hợp; không tự sửa quyền DB hiện tại.
Guard secret chỉ phát hiện một số cấu hình yếu, không đo entropy hay thay thế
secret manager. Pydantic error text/repr được che input nhạy cảm, nhưng không
log toàn bộ `model_dump()` của Settings. `.env` vẫn phải được bảo vệ ở filesystem.

Browser Auth có Origin lạ/`null` bị 403; request cross-site Fetch Metadata thiếu
Origin cũng bị chặn. CLI/Postman không có Origin vẫn hoạt động. Đây không thay
thế JWT, CORS, SameSite, HTTPS hoặc bảo vệ XSS. Nếu API/FE đổi domain phải cập
nhật hai origin kể trên; không giải quyết lỗi bằng wildcard.

## 5. Container API, PostgreSQL quản lý riêng

```powershell
docker compose -f compose.backend.yml config --quiet
docker compose -f compose.backend.yml build api
docker compose -f compose.backend.yml run --rm api python -m scripts.preflight
docker compose -f compose.backend.yml up -d api
```

Không chạy `compose config` không có `--quiet` rồi chia sẻ output: cấu hình đã
render có thể chứa secret. `up` không tự migrate hay seed. `--workers 1` tránh
nhân số bản model trong RAM; chỉ tăng worker sau benchmark đúng tải/model.

- Image mặc định CPU-only, giữ torch/torchvision cùng phiên bản trong requirements.
  Không dùng image này để khẳng định đã hỗ trợ GPU; GPU cần image/cấu hình riêng.
- API user UID/GID 10001, root filesystem read-only, /tmp tạm, uploads riêng,
  bỏ Linux capabilities và no-new-privileges. Port chỉ bind localhost.
- Docker Desktop: container dùng `host.docker.internal` để nối DB trên máy host;
  POSTGRES_PORT vẫn lấy từ `.env`. Linux/server khác: đặt CONTAINER_POSTGRES_HOST
  đúng host/network. Nếu có DATABASE_URL thì nó vẫn ưu tiên cao hơn POSTGRES_*:
  hostname trong URL phải truy cập được từ container, không mặc định localhost.
- Named volume `api_uploads` **mới và tách khỏi** `backend/storage/uploads` trên
  host. Không dùng DB có Scan cũ với volume trống: phải chuyển ảnh đã xác minh,
  giữ logical path và quyền UID 10001, hoặc cấu hình bind mount đúng kho ảnh.
  Không chạy `down -v` trên môi trường chứa dữ liệu cần giữ.
- Bind model root read-only, không auto-create thư mục nguồn. Database ModelVersion
  paths phải hợp lệ trong container; đường dẫn Windows tuyệt đối không portable.
  Phần kiểm chứng artifact/inference còn hoãn; các API không ML có thể test độc lập.
- Healthcheck `/health/ready` chỉ chứng nhận kết nối/schema, không xác nhận model.
- Uvicorn mặc định `--no-proxy-headers`. Production cần TLS termination tại reverse
  proxy riêng; khi cần forwarded headers, bật lại và chỉ trust IP proxy cụ thể,
  không dùng `--forwarded-allow-ips '*'` trên cổng truy cập trực tiếp.

Chưa cấu hình domain/TLS thực, ingress rate limit, quota disk, retention, secret
rotation hoặc browser E2E. Đó là các điều kiện vận hành phải nghiệm thu riêng.

## 6. Test hồi quy

Chỉ dùng PostgreSQL test tách biệt; fixture tạo/xóa DB có hậu tố `_test`.
Không đặt dữ liệu thật vào các DB tên test. Đặt TEST_DATABASE_URL đúng server test.

```powershell
$env:PG_BIN = 'C:\Program Files\PostgreSQL\18\bin'
python -m pytest -q --ignore=tests/test_predict_downloaded_samples.py -k 'not real_artifact_contract'
python -m mypy app tests scripts
python -m scripts.export_contract --check
```

Không cộng kết quả test phần mềm thành accuracy hay khả năng phát hiện lá.

## Tài liệu tham khảo triển khai

[Docker Compose services](https://docs.docker.com/reference/compose-file/services/)
cho user/read_only/volume/security/health configuration;
[PyTorch installation](https://pytorch.org/get-started/locally/) cho lựa chọn
CPU/GPU; [Pydantic settings](https://pydantic.dev/docs/validation/latest/concepts/pydantic_settings/)
cho nguồn biến môi trường/dotenv. Các cấu hình cụ thể phải được kiểm chứng trên
môi trường mục tiêu, không chỉ dựa vào tài liệu.
