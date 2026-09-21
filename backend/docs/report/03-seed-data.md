# 3. Seed dữ liệu quan trọng

## Seed lõi: `scripts.seed_week2`

Script idempotent: chạy lại chỉ thêm dữ liệu thiếu, không xóa và không ghi đè nội
dung Disease Info đã chỉnh sửa.

| Bảng | Dữ liệu |
| --- | --- |
| `users` | `admin_user`, `manager_user`, `technician_user`, `normal_user` |
| `disease_info` | 38 nhãn, khớp tuyệt đối `classes.json` của model |
| `model_versions` | EfficientNet-B0, MobileNetV2, ResNet50; manifest/checksum được kiểm tra trước khi ghi |

```powershell
$env:SEED_DEMO_PASSWORD='MatKhauDemo123!'
.\.venv\Scripts\python.exe -m scripts.seed_week2
Remove-Item Env:SEED_DEMO_PASSWORD
```

Chạy sau `alembic upgrade head`. Seed bị chặn khi `APP_ENV=production`.

## Farm demo: `scripts.seed_demo_farms`

File [demo_farms.json](../../seed_data/demo_farms.json) chứa Farm mẫu theo
`owner_username`. Script yêu cầu `manager_user` đã được tạo, thêm Farm còn thiếu
theo cặp owner/name và không cập nhật/xóa Farm hiện có.

```powershell
.\.venv\Scripts\python.exe -m scripts.seed_demo_farms
```

Chỉ thêm dữ liệu giả ở development/test. Với production, tạo Admin qua
`python -m scripts.bootstrap_admin` và nhập dữ liệu thực qua API/luồng nghiệp vụ.

## Không seed các bảng này

- `scans`, `scan_topk`, `scan_model_results`: là lịch sử/audit người dùng.
- `audit_events`: chỉ ứng dụng ghi append-only.
- `auth_rate_limits`: dữ liệu tạm, tự hết hạn.
- `disease_proposals`, `farm_members`: cần đúng actor/quy trình phân quyền.
