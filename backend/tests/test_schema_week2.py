"""Kiểm thử constraints/index quan trọng của schema Tuần 2."""

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app.models import DiseaseInfo, Farm, ModelVersion, Scan, ScanTopK, User


def test_users_have_required_roadmap_indexes(db_session):
    index_names = {
        item["name"] for item in inspect(db_session.bind).get_indexes("users")
    }
    assert {"idx_users_role", "idx_users_created_by"} <= index_names


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


def test_only_one_model_version_can_be_active(db_session):
    db_session.add_all(
        [
            ModelVersion(
                version_name="v1",
                file_path="models/v1.pt",
                classes_path="models/classes.json",
                is_active=True,
            ),
            ModelVersion(
                version_name="v2",
                file_path="models/v2.pt",
                classes_path="models/classes.json",
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
