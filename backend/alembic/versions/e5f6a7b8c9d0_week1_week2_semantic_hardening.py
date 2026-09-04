"""Thu hồi access token và soft-delete dữ liệu nền tảng Tuần 1-2.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("farms") as batch_op:
        batch_op.add_column(
            sa.Column("archived_at", sa.DateTime(), nullable=True)
        )
        batch_op.create_index(
            "idx_farms_archived_at",
            ["archived_at"],
            unique=False,
        )

    with op.batch_alter_table("disease_info") as batch_op:
        batch_op.add_column(
            sa.Column(
                "is_active",
                sa.Boolean(),
                server_default=sa.text("1"),
                nullable=False,
            )
        )
        batch_op.create_index(
            "idx_disease_info_is_active",
            ["is_active"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("disease_info") as batch_op:
        batch_op.drop_index("idx_disease_info_is_active")
        batch_op.drop_column("is_active")

    with op.batch_alter_table("farms") as batch_op:
        batch_op.drop_index("idx_farms_archived_at")
        batch_op.drop_column("archived_at")
