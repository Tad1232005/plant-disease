"""Multi-model inference, calibration metadata and per-model scan audit.

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-09-04

Giữ các cột legacy để nâng cấp database hiện có mà không làm mất lịch sử.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ràng buộc cũ chỉ cho một model active trên toàn hệ thống.
    with op.batch_alter_table("model_versions") as batch_op:
        batch_op.drop_index("idx_single_active_model")

    with op.batch_alter_table("model_versions", recreate="always") as batch_op:
        batch_op.alter_column(
            "version_name",
            existing_type=sa.String(length=20),
            type_=sa.String(length=50),
            existing_nullable=False,
        )
        batch_op.add_column(
            sa.Column(
                "model_type",
                sa.String(length=30),
                server_default="mobilenet_v2",
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "task",
                sa.String(length=40),
                server_default="disease_classification",
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("temperature_path", sa.String(length=255)))
        batch_op.add_column(
            sa.Column("temperature", sa.Float(), server_default="1.0", nullable=False)
        )
        batch_op.add_column(sa.Column("sha256", sa.String(length=64)))
        batch_op.add_column(sa.Column("macro_f1", sa.Float()))
        batch_op.add_column(sa.Column("ece", sa.Float()))
        batch_op.add_column(sa.Column("metrics_path", sa.String(length=255)))
        batch_op.add_column(
            sa.Column("is_enabled", sa.Boolean(), server_default=sa.text("1"), nullable=False)
        )
        batch_op.add_column(
            sa.Column(
                "updated_at",
                sa.DateTime(),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=False,
            )
        )
        batch_op.create_check_constraint(
            "ck_model_versions_model_type",
            "model_type IN ('mobilenet_v2', 'efficientnet_b0', 'resnet50')",
        )
        batch_op.create_check_constraint(
            "ck_model_versions_temperature", "temperature > 0"
        )
        batch_op.create_check_constraint(
            "ck_model_versions_macro_f1",
            "macro_f1 IS NULL OR (macro_f1 >= 0 AND macro_f1 <= 1)",
        )
        batch_op.create_check_constraint(
            "ck_model_versions_ece", "ece IS NULL OR (ece >= 0 AND ece <= 1)"
        )
        batch_op.create_index("idx_model_versions_model_type", ["model_type"])
        batch_op.create_index("idx_model_versions_is_enabled", ["is_enabled"])
        batch_op.create_index(
            "idx_one_active_version_per_model_type",
            ["model_type"],
            unique=True,
            postgresql_where=sa.text("is_active = true"),
            sqlite_where=sa.text("is_active = 1"),
        )

    # Model legacy chưa có artifact contract; seed mới sẽ đăng ký 3 version active.
    op.execute(sa.text("UPDATE model_versions SET is_active = 0"))

    with op.batch_alter_table("farm_members", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("added_by", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_farm_members_added_by_users",
            "users",
            ["added_by"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("scans", recreate="always") as batch_op:
        batch_op.alter_column(
            "model_version",
            existing_type=sa.String(length=20),
            type_=sa.String(length=50),
            existing_nullable=True,
        )
        batch_op.add_column(sa.Column("primary_model_version_id", sa.Integer()))
        batch_op.add_column(
            sa.Column("inference_mode", sa.String(length=20), server_default="legacy", nullable=False)
        )
        batch_op.add_column(
            sa.Column("validation_status", sa.String(length=30), server_default="accepted", nullable=False)
        )
        batch_op.add_column(sa.Column("rejection_reason", sa.String(length=50)))
        batch_op.add_column(
            sa.Column("agreement_status", sa.String(length=30), server_default="single_model", nullable=False)
        )
        batch_op.add_column(sa.Column("top1_top2_margin", sa.Float()))
        batch_op.add_column(sa.Column("ensemble_entropy", sa.Float()))
        batch_op.add_column(sa.Column("js_divergence", sa.Float()))
        batch_op.add_column(sa.Column("energy_score", sa.Float()))
        batch_op.add_column(sa.Column("ood_score", sa.Float()))
        batch_op.add_column(sa.Column("policy_version", sa.String(length=50)))
        batch_op.create_foreign_key(
            "fk_scans_primary_model_version",
            "model_versions",
            ["primary_model_version_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_check_constraint(
            "ck_scans_inference_mode",
            "inference_mode IN ('legacy', 'basic', 'standard', 'advanced')",
        )
        batch_op.create_check_constraint(
            "ck_scans_validation_status",
            "validation_status IN ('accepted', 'low_confidence', 'ambiguous', 'model_error')",
        )
        batch_op.create_check_constraint(
            "ck_scans_agreement_status",
            "agreement_status IN ('single_model', 'agreed', 'disagreed', 'degraded')",
        )
        batch_op.create_check_constraint(
            "ck_scans_margin",
            "top1_top2_margin IS NULL OR (top1_top2_margin >= 0 AND top1_top2_margin <= 1)",
        )
        batch_op.create_check_constraint(
            "ck_scans_entropy",
            "ensemble_entropy IS NULL OR (ensemble_entropy >= 0 AND ensemble_entropy <= 1)",
        )
        batch_op.create_check_constraint(
            "ck_scans_js_divergence",
            "js_divergence IS NULL OR (js_divergence >= 0 AND js_divergence <= 1)",
        )
        batch_op.create_check_constraint(
            "ck_scans_ood_score",
            "ood_score IS NULL OR (ood_score >= 0 AND ood_score <= 1)",
        )
        batch_op.create_index(
            "idx_scans_primary_model_version_id", ["primary_model_version_id"]
        )
        batch_op.create_index("idx_scans_inference_mode", ["inference_mode"])
        batch_op.create_index("idx_scans_validation_status", ["validation_status"])

    # Dữ liệu lịch sử confidence thấp được đánh dấu rõ sau khi thêm cột.
    op.execute(
        sa.text(
            "UPDATE scans SET validation_status = 'low_confidence', "
            "rejection_reason = 'legacy_low_confidence' WHERE is_valid_leaf = 0"
        )
    )

    op.create_table(
        "scan_model_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("scan_id", sa.Integer(), nullable=False),
        sa.Column("model_version_id", sa.Integer(), nullable=False),
        sa.Column("execution_order", sa.Integer(), nullable=False),
        sa.Column("predicted_label", sa.String(length=50)),
        sa.Column("confidence", sa.Float()),
        sa.Column("top1_top2_margin", sa.Float()),
        sa.Column("entropy", sa.Float()),
        sa.Column("energy_score", sa.Float()),
        sa.Column("accepted", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("latency_ms", sa.Float()),
        sa.Column("error_code", sa.String(length=50)),
        sa.Column("topk_json", sa.Text()),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.CheckConstraint("execution_order BETWEEN 1 AND 3", name="ck_scan_model_result_order"),
        sa.CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_scan_model_result_confidence",
        ),
        sa.CheckConstraint(
            "top1_top2_margin IS NULL OR (top1_top2_margin >= 0 AND top1_top2_margin <= 1)",
            name="ck_scan_model_result_margin",
        ),
        sa.CheckConstraint(
            "entropy IS NULL OR (entropy >= 0 AND entropy <= 1)",
            name="ck_scan_model_result_entropy",
        ),
        sa.CheckConstraint("latency_ms IS NULL OR latency_ms >= 0", name="ck_scan_model_result_latency"),
        sa.ForeignKeyConstraint(["scan_id"], ["scans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["model_version_id"], ["model_versions.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scan_id", "model_version_id", name="uq_scan_model_result_model"),
    )
    op.create_index("idx_scan_model_results_scan_id", "scan_model_results", ["scan_id"])
    op.create_index(
        "idx_scan_model_results_model_version_id", "scan_model_results", ["model_version_id"]
    )
    op.create_index("idx_scan_model_results_created_at", "scan_model_results", ["created_at"])


def downgrade() -> None:
    op.drop_index("idx_scan_model_results_created_at", table_name="scan_model_results")
    op.drop_index("idx_scan_model_results_model_version_id", table_name="scan_model_results")
    op.drop_index("idx_scan_model_results_scan_id", table_name="scan_model_results")
    op.drop_table("scan_model_results")

    with op.batch_alter_table("scans", recreate="always") as batch_op:
        batch_op.drop_index("idx_scans_validation_status")
        batch_op.drop_index("idx_scans_inference_mode")
        batch_op.drop_index("idx_scans_primary_model_version_id")
        batch_op.drop_constraint("fk_scans_primary_model_version", type_="foreignkey")
        for name in (
            "ck_scans_ood_score", "ck_scans_js_divergence", "ck_scans_entropy",
            "ck_scans_margin", "ck_scans_agreement_status",
            "ck_scans_validation_status", "ck_scans_inference_mode",
        ):
            batch_op.drop_constraint(name, type_="check")
        for column in (
            "policy_version", "ood_score", "energy_score", "js_divergence",
            "ensemble_entropy", "top1_top2_margin", "agreement_status",
            "rejection_reason", "validation_status", "inference_mode",
            "primary_model_version_id",
        ):
            batch_op.drop_column(column)
        batch_op.alter_column(
            "model_version",
            existing_type=sa.String(length=50),
            type_=sa.String(length=20),
            existing_nullable=True,
        )

    with op.batch_alter_table("farm_members", recreate="always") as batch_op:
        batch_op.drop_constraint("fk_farm_members_added_by_users", type_="foreignkey")
        batch_op.drop_column("added_by")

    # Schema cũ chỉ cho một active version toàn cục; tắt hết để downgrade luôn an toàn.
    op.execute(sa.text("UPDATE model_versions SET is_active = 0"))
    with op.batch_alter_table("model_versions", recreate="always") as batch_op:
        batch_op.drop_index("idx_one_active_version_per_model_type")
        batch_op.drop_index("idx_model_versions_is_enabled")
        batch_op.drop_index("idx_model_versions_model_type")
        batch_op.drop_constraint("ck_model_versions_ece", type_="check")
        batch_op.drop_constraint("ck_model_versions_macro_f1", type_="check")
        batch_op.drop_constraint("ck_model_versions_temperature", type_="check")
        batch_op.drop_constraint("ck_model_versions_model_type", type_="check")
        for column in (
            "updated_at", "is_enabled", "metrics_path", "ece", "macro_f1",
            "sha256", "temperature", "temperature_path", "task", "model_type",
        ):
            batch_op.drop_column(column)
        batch_op.alter_column(
            "version_name",
            existing_type=sa.String(length=50),
            type_=sa.String(length=20),
            existing_nullable=False,
        )
        batch_op.create_index(
            "idx_single_active_model",
            ["is_active"],
            unique=True,
            postgresql_where=sa.text("is_active = true"),
            sqlite_where=sa.text("is_active = 1"),
        )
