"""Kiểm thử seed data Tuần 1-2."""

from app.models import DiseaseInfo, ModelVersion, User
from scripts.seed_week2 import DEMO_USERS, load_labels, seed_database


def run_seed(db_session):
    labels = load_labels("app/ml_assets/classes.json")
    summary = seed_database(
        db_session,
        labels=labels,
        demo_password="SeedTest123!",
        model_path="app/ml_assets/best_model.pt",
        classes_path="app/ml_assets/classes.json",
    )
    return labels, summary


def test_seed_creates_demo_users_all_classes_and_active_model(db_session):
    labels, summary = run_seed(db_session)

    assert summary.users_created == 4
    assert summary.diseases_created == len(labels) == 38
    assert summary.model_versions_created == 1
    assert {user.role for user in db_session.query(User).all()} == {
        item["role"] for item in DEMO_USERS
    }
    assert {
        item.label_key for item in db_session.query(DiseaseInfo).all()
    } == set(labels)
    assert all(
        item.description and item.treatment
        for item in db_session.query(DiseaseInfo).all()
    )
    assert db_session.query(
        ModelVersion).filter_by(is_active=True).count() == 1


def test_seed_is_idempotent_and_does_not_overwrite_content(db_session):
    labels, _ = run_seed(db_session)
    first_disease = db_session.query(DiseaseInfo).filter_by(
        label_key=labels[0]
    ).one()
    first_disease.description = "Nội dung đã được Admin chỉnh sửa"
    db_session.commit()

    _, second_summary = run_seed(db_session)

    assert second_summary.users_created == 0
    assert second_summary.diseases_created == 0
    assert second_summary.model_versions_created == 0
    assert db_session.query(User).count() == 4
    assert db_session.query(DiseaseInfo).count() == len(labels)
    assert db_session.get(DiseaseInfo, first_disease.id).description == (
        "Nội dung đã được Admin chỉnh sửa"
    )
