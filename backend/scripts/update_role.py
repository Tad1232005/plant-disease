"""Script tạm để cập nhật role user trong DB."""

import sqlite3

conn = sqlite3.connect("plant_disease.db")
conn.execute("UPDATE users SET role = 'admin' WHERE username = 'testuser1'")
conn.commit()

# Kiểm tra lại ngay
result = conn.execute(
    "SELECT username, role FROM users WHERE username = 'testuser1'"
).fetchone()
print("Kết quả sau khi cập nhật:", result)

conn.close()
