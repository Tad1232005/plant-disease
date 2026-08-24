"""Harden Auth và schema nền tảng Tuần 1-2.

Revision ID: 8b20a1c2d3e4
Revises: fca11835f6c1
Create Date: 2026-08-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8b20a1c2d3e4"
down_revision: Union[str, None] = "fca11835f6c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users", recreate="always") as batch_op:
        batch_op.add_column(
            sa.Column(
                "created_by",
                sa.Integer(),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "token_version",
                sa.Integer(),
                server_default="0",
                nullable=False,
            )
        )
        batch_op.create_foreign_key(
            "fk_users_created_by_users",
            "users",
            ["created_by"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("idx_users_role", ["role"], unique=False)
        batch_op.create_index(
            "idx_users_created_by", ["created_by"], unique=False
        )
        batch_op.drop_index("ix_users_id")

    with op.batch_alter_table("disease_info", recreate="always") as batch_op:
        batch_op.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=False,
            )
        )
        batch_op.drop_index("ix_disease_info_id")

    with op.batch_alter_table("model_versions") as batch_op:
        batch_op.add_column(
            sa.Column("classes_path", sa.String(length=255), nullable=True)
        )

    with op.batch_alter_table("farms") as batch_op:
        batch_op.drop_index("ix_farms_id")

    with op.batch_alter_table("scans") as batch_op:
        batch_op.drop_index("ix_scans_id")
        batch_op.drop_index("ix_scans_user_id")
        batch_op.drop_index("ix_scans_farm_id")
        batch_op.drop_index("ix_scans_created_at")
        batch_op.drop_index("ix_scans_predicted_label")

    with op.batch_alter_table("scan_topk", recreate="always") as batch_op:
        batch_op.create_unique_constraint(
            "uq_scan_topk_scan_rank", ["scan_id", "rank"]
        )
        batch_op.drop_index("ix_scan_topk_id")


def downgrade() -> None:
    with op.batch_alter_table("scan_topk", recreate="always") as batch_op:
        batch_op.drop_constraint("uq_scan_topk_scan_rank", type_="unique")
        batch_op.create_index("ix_scan_topk_id", ["id"], unique=False)

    with op.batch_alter_table("scans") as batch_op:
        batch_op.create_index(
            "ix_scans_predicted_label", ["predicted_label"], unique=False
        )
        batch_op.create_index(
            "ix_scans_created_at", ["created_at"], unique=False
        )
        batch_op.create_index("ix_scans_farm_id", ["farm_id"], unique=False)
        batch_op.create_index("ix_scans_user_id", ["user_id"], unique=False)
        batch_op.create_index("ix_scans_id", ["id"], unique=False)

    with op.batch_alter_table("farms") as batch_op:
        batch_op.create_index("ix_farms_id", ["id"], unique=False)

    with op.batch_alter_table("model_versions") as batch_op:
        batch_op.drop_column("classes_path")

    with op.batch_alter_table("disease_info", recreate="always") as batch_op:
        batch_op.create_index("ix_disease_info_id", ["id"], unique=False)
        batch_op.drop_column("created_at")

    with op.batch_alter_table("users", recreate="always") as batch_op:
        batch_op.create_index("ix_users_id", ["id"], unique=False)
        batch_op.drop_index("idx_users_created_by")
        batch_op.drop_index("idx_users_role")
        batch_op.drop_constraint("fk_users_created_by_users", type_="foreignkey")
        batch_op.drop_column("token_version")
        batch_op.drop_column("created_by")
