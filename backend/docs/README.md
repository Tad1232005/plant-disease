# Tài liệu backend

Đọc từ hiện trạng mới nhất trước; các báo cáo theo tuần là mốc lịch sử, không
phải hướng dẫn triển khai thay thế tài liệu mới hơn.

| Nhu cầu | Tài liệu |
| --- | --- |
| Cài đặt, chạy local, cấu trúc thư mục | [Backend README](../README.md) |
| Thay đổi không ML ở rc.2 (rate limit, đổi role, logging) | [NON_ML_COMPLETION.md](week8/NON_ML_COMPLETION.md) |
| Preflight, backup, migration, bootstrap Admin, Docker | [DEPLOYMENT.md](week8/DEPLOYMENT.md) |
| Kết quả triển khai thử và giới hạn nghiệm thu rc.1 | [REPORT.md tuần 8](week8/REPORT.md) |
| Hợp đồng frontend/OpenAPI ở mốc tuần 7 | [FRONTEND_HANDOFF.md](week7/FRONTEND_HANDOFF.md) |
| API và workflow không ML tuần 5–6 | [week5-week6-non-ml.md](week5-week6-non-ml.md) |
| Chính sách chọn model, ảnh tải về, kiểm thử inference | [predict-selection-audit/REPORT.md](predict-selection-audit/REPORT.md) |
| Rủi ro nhận diện lá/OOD và thử nghiệm input policy | [week3-rescue/REPORT.md](week3-rescue/REPORT.md) |

Lưu ý: code/test và database ứng dụng có thể ở revision khác nhau. Kiểm tra
`python -m scripts.preflight` trước khi chạy API nghiệp vụ hoặc migration; lệnh
này chỉ đọc. Không suy diễn rằng kết quả test trên DB tạm đã nâng DB ứng dụng.
