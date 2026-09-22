"""Kiểm thử constraints/index quan trọng của schema Tuần 2."""

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app.models import (
    DiseaseInfo,
    Farm,
    FarmMember,
    ModelVersion,
    Scan,
    ScanModelResult,
    ScanTopK,
    User,
)


def test_users_have_required_roadmap_indexes(db_session):
    index_names = {
        item["name"] for item in inspect(db_session.bind).get_indexes("users")
    }
    assert {"idx_users_role", "idx_users_created_by"} <= index_names


def test_users_have_created_by_column(db_session):
    column_names = {
        item["name"] for item in inspect(db_session.bind).get_columns("users")
    }
    assert "created_by" in column_names


def test_soft_delete_columns_and_indexes_exist(db_session):
    inspector = inspect(db_session.bind)
    farm_columns = {
        item["name"] for item in inspector.get_columns("farms")
    }
    disease_columns = {
        item["name"] for item in inspector.get_columns("disease_info")
    }
    farm_indexes = {
        item["name"] for item in inspector.get_indexes("farms")
    }
    disease_indexes = {
        item["name"] for item in inspector.get_indexes("disease_info")
    }

    assert "archived_at" in farm_columns
    assert "is_active" in disease_columns
    assert "idx_farms_archived_at" in farm_indexes
    assert "idx_disease_info_is_active" in disease_indexes


def test_user_role_check_constraint(db_session):
    db_session.add(
        User(
            username="invalid_role",
            email="invalid@test.local",
            password_hash="hash",
            role="superuser",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_one_active_version_is_allowed_per_model_type(db_session):
    db_session.add_all(
        [
            ModelVersion(
                version_name="v1",
                model_type="efficientnet_b0",
                file_path="models/v1.pt",
                classes_path="models/classes.json",
                is_active=True,
            ),
            ModelVersion(
                version_name="v2",
                model_type="mobilenet_v2",
                file_path="models/v2.pt",
                classes_path="models/classes.json",
                is_active=True,
            ),
        ]
    )
    db_session.commit()
    assert db_session.query(ModelVersion).filter_by(is_active=True).count() == 2


def test_two_active_versions_of_same_model_type_are_rejected(db_session):
    db_session.add_all(
        [
            ModelVersion(
                version_name="efficient-v1",
                model_type="efficientnet_b0",
                file_path="models/v1.pt",
                is_active=True,
            ),
            ModelVersion(
                version_name="efficient-v2",
                model_type="efficientnet_b0",
                file_path="models/v2.pt",
                is_active=True,
            ),
        ]
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_model_accuracy_check_constraint(db_session):
    db_session.add(
        ModelVersion(
            version_name="invalid-accuracy",
            model_type="resnet50",
            file_path="models/invalid.pt",
            accuracy=1.1,
            is_active=False,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_disease_severity_check_constraint(db_session):
    db_session.add(
        DiseaseInfo(
            label_key="Invalid___Severity",
            disease_name="Invalid",
            severity_level="critical",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_farm_owner_foreign_key_constraint(db_session):
    db_session.add(Farm(owner_id=999_999, name="Orphan farm"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_scan_confidence_check_constraint(db_session, normal_user):
    db_session.add(
        Scan(
            user_id=normal_user.id,
            image_path="storage/uploads/invalid-confidence.jpg",
            confidence=-0.1,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_scan_topk_rank_is_unique_per_scan(db_session, normal_user):
    scan = Scan(
        user_id=normal_user.id,
        image_path="storage/uploads/test.jpg",
        confidence=0.8,
    )
    db_session.add(scan)
    db_session.flush()
    db_session.add_all(
        [
            ScanTopK(scan_id=scan.id, label="a", confidence=0.8, rank=1),
            ScanTopK(scan_id=scan.id, label="b", confidence=0.2, rank=1),
        ]
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_scan_topk_rank_and_confidence_checks(db_session, normal_user):
    scan = Scan(
        user_id=normal_user.id,
        image_path="storage/uploads/invalid-topk.jpg",
        confidence=0.8,
    )
    db_session.add(scan)
    db_session.flush()
    db_session.add(
        ScanTopK(scan_id=scan.id, label="invalid", confidence=1.1, rank=4)
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_farm_member_is_unique_per_farm_and_user(
    db_session,
    manager_user,
    normal_user,
):
    farm = Farm(owner_id=manager_user.id, name="Unique Member Farm")
    db_session.add(farm)
    db_session.flush()
    db_session.add_all(
        [
            FarmMember(farm_id=farm.id, user_id=normal_user.id),
            FarmMember(farm_id=farm.id, user_id=normal_user.id),
        ]
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_scan_model_result_is_unique_per_scan_and_model(
    db_session, normal_user
):
    model = ModelVersion(
        version_name="audit-v1",
        model_type="mobilenet_v2",
        file_path="models/audit.pt",
        is_active=True,
    )
    scan = Scan(user_id=normal_user.id, image_path="storage/uploads/audit.jpg")
    db_session.add_all([model, scan])
    db_session.flush()
    db_session.add_all(
        [
            ScanModelResult(
                scan_id=scan.id,
                model_version_id=model.id,
                execution_order=1,
            ),
            ScanModelResult(
                scan_id=scan.id,
                model_version_id=model.id,
                execution_order=2,
            ),
        ]
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_multi_model_columns_and_indexes_exist(db_session):
    inspector = inspect(db_session.bind)
    model_columns = {item["name"] for item in inspector.get_columns("model_versions")}
    scan_columns = {item["name"] for item in inspector.get_columns("scans")}
    model_indexes = {item["name"] for item in inspector.get_indexes("model_versions")}
    assert {
        "model_type", "temperature", "temperature_path", "sha256", "is_enabled"
    } <= model_columns
    assert {
        "primary_model_version_id", "inference_mode", "validation_status",
        "agreement_status", "ood_score",
    } <= scan_columns
    assert "idx_one_active_version_per_model_type" in model_indexes
    assert inspector.has_table("scan_model_results")
