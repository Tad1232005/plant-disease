"""Kiểm thử seed core data và ba model version độc lập."""

from app.core.config import settings
from app.models import DiseaseInfo, ModelVersion, User
from app.services.model_artifact_service import (
    ModelArtifactSpec,
    _bundle_digest,
    discover_artifacts,
)
from scripts.seed_week2 import DEMO_USERS, seed_database


def lightweight_specs(labels: list[str]) -> list[ModelArtifactSpec]:
    return [
        ModelArtifactSpec(
            version_name=f"{model_type}-test-v1",
            model_type=model_type,
            task="disease_classification",
            file_path=f"models/{model_type}/model.pt",
            classes_path=f"models/{model_type}/classes.json",
            temperature_path=f"models/{model_type}/temperature.json",
            temperature=1.0,
            sha256=character * 64,
            classes=tuple(labels),
        )
        for model_type, character in (
            ("efficientnet_b0", "a"),
            ("mobilenet_v2", "b"),
            ("resnet50", "c"),
        )
    ]


def run_seed(db_session):
    labels = list(discover_artifacts(settings.MODEL_ARTIFACT_ROOT)[0].classes)
    summary = seed_database(
        db_session,
        labels=labels,
        demo_password="SeedTest123!",
        model_specs=lightweight_specs(labels),
    )
    return labels, summary


def test_seed_creates_demo_users_all_classes_and_three_active_models(db_session):
    labels, summary = run_seed(db_session)
    assert summary.users_created == 4
    assert summary.diseases_created == len(labels) == 38
    assert summary.model_versions_created == 3
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
    active = db_session.query(ModelVersion).filter_by(is_active=True).all()
    assert {item.model_type for item in active} == {
        "efficientnet_b0", "mobilenet_v2", "resnet50"
    }


def test_seed_is_idempotent_and_does_not_overwrite_content(db_session):
    labels, _ = run_seed(db_session)
    first_disease = db_session.query(DiseaseInfo).filter_by(label_key=labels[0]).one()
    first_disease.description = "Nội dung đã được Admin chỉnh sửa"
    db_session.commit()
    _, second_summary = run_seed(db_session)
    assert second_summary == second_summary.__class__(0, 0, 0)
    assert db_session.query(User).count() == 4
    assert db_session.query(DiseaseInfo).count() == len(labels)
    assert db_session.query(ModelVersion).count() == 3
    assert db_session.get(DiseaseInfo, first_disease.id).description == (
        "Nội dung đã được Admin chỉnh sửa"
    )


def test_real_artifact_contract_has_three_matching_class_orders():
    specs = discover_artifacts(settings.MODEL_ARTIFACT_ROOT)
    assert len(specs) == 3
    assert all(len(item.classes) == 38 for item in specs)
    assert len({item.classes for item in specs}) == 1
    assert all(len(item.sha256) == 64 for item in specs)


def test_bundle_checksum_is_independent_of_json_formatting(tmp_path):
    model_file = tmp_path / "model.pt"
    metadata_file = tmp_path / "metadata.json"
    model_file.write_bytes(b"stable-model-bytes")
    metadata_file.write_text('{"temperature": 1.5, "classes": ["a", "b"]}\n')
    first = _bundle_digest([model_file, metadata_file])

    metadata_file.write_text(
        '{\r\n  "classes": ["a", "b"],\r\n  "temperature": 1.5\r\n}',
        encoding="utf-8",
    )
    second = _bundle_digest([model_file, metadata_file])

    assert second == first
