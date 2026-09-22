"""Shared, expiring Auth request counters (no model changes)."""
from alembic import op
import sqlalchemy as sa

revision = "d0e1f2a3b4c5"
down_revision = "c9d0e1f2a3b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "auth_rate_limits",
        sa.Column("bucket_key", sa.String(64), primary_key=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("attempts > 0", name="ck_auth_rate_limits_attempts"),
    )
    op.create_index("idx_auth_rate_limits_expiry", "auth_rate_limits", ["expires_at"])


def downgrade() -> None:
    op.drop_table("auth_rate_limits")
