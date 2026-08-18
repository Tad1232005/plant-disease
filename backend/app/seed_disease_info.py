"""Script nạp dữ liệu bệnh ban đầu vào bảng disease_info.

Chạy bằng lệnh: python -m app.seed_disease_info
"""

import json

from app.db.session import SessionLocal
from app.models.disease_info import DiseaseInfo

# Đọc 38 nhãn từ classes.json để đảm bảo label_key khớp chính xác với model
with open("app/ml_assets/classes.json", "r", encoding="utf-8") as f:
    CLASSES = json.load(f)


def seed():
    """Tạo bản ghi disease_info rỗng cho từng nhãn nếu chưa tồn tại."""
    db = SessionLocal()
    try:
        for label in CLASSES:
            exists = db.query(DiseaseInfo).filter(
                DiseaseInfo.label_key == label).first()
            if not exists:
                db.add(DiseaseInfo(
                    label_key=label,
                    disease_name=label.replace("___", " - ").replace("_", " "),
                    description="Chưa cập nhật mô tả",
                    treatment="Chưa cập nhật gợi ý xử lý",
                    severity_level="medium",
                ))
        db.commit()
        print(f"Đã seed xong {len(CLASSES)} nhãn bệnh")
    finally:
        db.close()


if __name__ == "__main__":
    seed()