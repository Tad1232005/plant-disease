"""Add composite indexes on scans for pagination performance.

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
Create Date: 2026-09-22

Them composite index (user_id, created_at) va (farm_id, created_at)
de tang toc cac query lich su scan pho bien nhat.
"""

from alembic import op

revision = "e1f2a3b4c5d6"
down_revision = "d0e1f2a3b4c5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Composite index for GET /scans/history (user_id filter + created_at order)
    op.create_index(
        "idx_scans_user_created",
        "scans",
        ["user_id", "created_at"],
        unique=False,
    )
    # Composite index for GET /scans/history?farm_id=X (farm_id filter + created_at order)
    op.create_index(
        "idx_scans_farm_created",
        "scans",
        ["farm_id", "created_at"],
        unique=False,
        postgresql_where="farm_id IS NOT NULL",
    )


def downgrade() -> None:
    op.drop_index("idx_scans_farm_created", table_name="scans")
    op.drop_index("idx_scans_user_created", table_name="scans")
