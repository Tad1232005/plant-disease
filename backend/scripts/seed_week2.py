"""Seed dữ liệu nền tảng cho backend Tuần 1-2.

Chạy sau khi đã migrate database::

    python -m scripts.seed_week2

Script có thể chạy lại an toàn: chỉ thêm bản ghi còn thiếu và không ghi đè dữ
liệu người dùng hoặc nội dung bệnh đã được chỉnh sửa trong hệ thống.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
import sys
from typing import Sequence

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import DiseaseInfo, ModelVersion, User
from app.services.model_artifact_service import (
    ModelArtifactSpec,
    discover_artifacts,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


DEMO_USERS = (
    {
        "username": "admin_user",
        "email": "admin@test.local",
        "role": "admin",
        "full_name": "Quản trị viên demo",
    },
    {
        "username": "manager_user",
        "email": "manager@test.local",
        "role": "manager",
        "full_name": "Quản lý trang trại demo",
    },
    {
        "username": "technician_user",
        "email": "technician@test.local",
        "role": "technician",
        "full_name": "Kỹ thuật viên demo",
    },
    {
        "username": "normal_user",
        "email": "user@test.local",
        "role": "user",
        "full_name": "Người dùng demo",
    },
)

_CROP_NAMES = {
    "Apple": "Táo",
    "Blueberry": "Việt quất",
    "Cherry_(including_sour)": "Anh đào",
    "Corn_(maize)": "Ngô",
    "Grape": "Nho",
    "Orange": "Cam",
    "Peach": "Đào",
    "Pepper,_bell": "Ớt chuông",
    "Potato": "Khoai tây",
    "Raspberry": "Mâm xôi",
    "Soybean": "Đậu tương",
    "Squash": "Bí",
    "Strawberry": "Dâu tây",
    "Tomato": "Cà chua",
}

_CONDITION_NAMES = {
    "Apple_scab": "Bệnh ghẻ táo",
    "Black_rot": "Bệnh thối đen",
    "Cedar_apple_rust": "Bệnh gỉ sắt tuyết tùng - táo",
    "Powdery_mildew": "Bệnh phấn trắng",
    "Cercospora_leaf_spot Gray_leaf_spot": "Bệnh đốm lá xám Cercospora",
    "Common_rust_": "Bệnh gỉ sắt thông thường",
    "Northern_Leaf_Blight": "Bệnh cháy lá phương Bắc",
    "Esca_(Black_Measles)": "Bệnh Esca (sởi đen)",
    "Leaf_blight_(Isariopsis_Leaf_Spot)": "Bệnh cháy lá Isariopsis",
    "Haunglongbing_(Citrus_greening)": "Bệnh vàng lá gân xanh",
    "Bacterial_spot": "Bệnh đốm vi khuẩn",
    "Early_blight": "Bệnh cháy lá sớm",
    "Late_blight": "Bệnh mốc sương",
    "Leaf_scorch": "Bệnh cháy mép lá",
    "Leaf_Mold": "Bệnh mốc lá",
    "Septoria_leaf_spot": "Bệnh đốm lá Septoria",
    "Spider_mites Two-spotted_spider_mite": "Nhện đỏ hai chấm",
    "Target_Spot": "Bệnh đốm vòng",
    "Tomato_Yellow_Leaf_Curl_Virus": "Virus xoăn vàng lá cà chua",
    "Tomato_mosaic_virus": "Virus khảm cà chua",
    "healthy": "Khỏe mạnh",
}

_HIGH_SEVERITY = {
    "Haunglongbing_(Citrus_greening)",
    "Late_blight",
    "Tomato_Yellow_Leaf_Curl_Virus",
}


@dataclass(frozen=True)
class SeedSummary:
    """Số bản ghi thực sự được tạo trong một lần chạy seed."""

    users_created: int
    diseases_created: int
    model_versions_created: int


def disease_defaults(label: str) -> dict[str, str]:
    """Tạo nội dung nền tảng có thể dùng ngay từ một label của model."""
    crop_key, separator, condition_key = label.partition("___")
    if not separator:
        raise RuntimeError(f"Label không đúng định dạng"
                           f" <crop>___<condition>: {label}")

    crop_name = _CROP_NAMES.get(crop_key, crop_key.replace("_", " "))
    condition_name = _CONDITION_NAMES.get(
        condition_key,
        condition_key.replace("_", " "),
    )
    is_healthy = condition_key == "healthy"

    if is_healthy:
        description = f"Lá {crop_name.lower()} không biểu hiện "
        " dấu hiệu bệnh rõ ràng."
        treatment = (
            "Tiếp tục theo dõi định kỳ, tưới tiêu hợp lý và duy trì vệ sinh "
            "khu vực trồng."
        )
        severity_level = "low"
    else:
        description = (
            f"Mẫu lá {crop_name.lower()} được nhận diện thuộc nhóm "
            f"{condition_name.lower()}."
        )
        treatment = (
            "Cách ly cây có triệu chứng, loại bỏ phần bị bệnh và tham khảo "
            "kỹ thuật viên nông nghiệp trước khi dùng thuốc bảo vệ thực vật."
        )
        severity_level = "high" if condition_key in _HIGH_SEVERITY else "medium"

    return {
        "label_key": label,
        "disease_name": f"{condition_name} - {crop_name}",
        "description": description,
        "treatment": treatment,
        "severity_level": severity_level,
    }


def seed_database(
    db: Session,
    *,
    labels: Sequence[str],
    demo_password: str,
    model_specs: Sequence[ModelArtifactSpec],
) -> SeedSummary:
    """Seed một session và commit đúng một transaction."""
    users_created = 0
    diseases_created = 0
    model_versions_created = 0

    try:
        for demo_user in DEMO_USERS:
            username = demo_user["username"]
            existing_user = db.query(User).filter(
                User.username == username).first()
            if existing_user is not None:
                continue

            email = demo_user["email"]
            if db.query(User).filter(User.email == email).first() is not None:
                raise RuntimeError(
                    f"Email seed {email} đã thuộc về một username khác"
                )
            db.add(
                User(
                    **demo_user,
                    password_hash=hash_password(demo_password),
                )
            )
            users_created += 1

        existing_labels = {
            row[0]
            for row in db.query(DiseaseInfo.label_key)
            .filter(DiseaseInfo.label_key.in_(list(labels)))
            .all()
        }
        for label in labels:
            if label not in existing_labels:
                db.add(DiseaseInfo(**disease_defaults(label)))
                diseases_created += 1

        for spec in model_specs:
            model_version = (
                db.query(ModelVersion)
                .filter(ModelVersion.version_name == spec.version_name)
                .first()
            )
            if model_version is not None:
                if (
                    model_version.model_type != spec.model_type
                    or model_version.task != spec.task
                    or model_version.sha256 != spec.sha256
                ):
                    raise RuntimeError(
                        f"Version name collision với artifact khác: {spec.version_name}"
                    )
                # Cho phép chuyển database sang installation path khác khi bundle
                # vẫn có cùng checksum; không thay activation do Admin quyết định.
                model_version.file_path = spec.file_path
                model_version.classes_path = spec.classes_path
                model_version.temperature_path = spec.temperature_path
                model_version.temperature = spec.temperature
                continue
            has_active_model = (
                db.query(ModelVersion)
                .filter(
                    ModelVersion.model_type == spec.model_type,
                    ModelVersion.is_active.is_(True),
                )
                .first()
                is not None
            )
            db.add(
                ModelVersion(
                    version_name=spec.version_name,
                    model_type=spec.model_type,
                    task=spec.task,
                    file_path=spec.file_path,
                    classes_path=spec.classes_path,
                    temperature_path=spec.temperature_path,
                    temperature=spec.temperature,
                    sha256=spec.sha256,
                    is_active=not has_active_model,
                )
            )
            model_versions_created += 1

        db.commit()
    except Exception:
        db.rollback()
        raise

    return SeedSummary(
        users_created=users_created,
        diseases_created=diseases_created,
        model_versions_created=model_versions_created,
    )


def run() -> SeedSummary:
    """Nạp cấu hình, mở session và chạy seed."""
    model_specs = discover_artifacts(settings.MODEL_ARTIFACT_ROOT)
    labels = list(model_specs[0].classes)
    demo_password = os.getenv("SEED_DEMO_PASSWORD", "Demo123321!")
    db = SessionLocal()
    try:
        summary = seed_database(
            db,
            labels=labels,
            demo_password=demo_password,
            model_specs=model_specs,
        )
    finally:
        db.close()

    print(
        "Seed Tuần 1-2 hoàn tất: "
        f"+{summary.users_created} user, "
        f"+{summary.diseases_created} disease_info, "
        f"+{summary.model_versions_created} model_version."
    )
    return summary


if __name__ == "__main__":
    run()
