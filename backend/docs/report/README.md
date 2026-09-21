# Báo cáo và hướng dẫn vận hành backend

Thư mục này dành cho thành viên backend, frontend và kiểm thử. Các lệnh dùng
PowerShell trên Windows, chạy từ thư mục `backend/`.

| Tài liệu | Mục đích |
| --- | --- |
| [01-local-setup.md](01-local-setup.md) | Cài môi trường, PostgreSQL, migration, seed và chạy API |
| [02-pgadmin4.md](02-pgadmin4.md) | Register server trên pgAdmin 4 và truy vấn an toàn |
| [03-seed-data.md](03-seed-data.md) | Dữ liệu seed, thứ tự chạy và nguyên tắc không ghi đè |
| [04-test-and-handoff.md](04-test-and-handoff.md) | Kiểm thử, API thực tế và các giới hạn ML cần biết |
| [05-api-manual-test.md](05-api-manual-test.md) | Kịch bản test thủ công cho từng nhóm API |

Không đưa `.env`, mật khẩu, access/refresh token, ảnh người dùng hoặc file
`model.pt` vào Git hay tài liệu chia sẻ công khai.
