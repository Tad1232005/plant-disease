"""Preserve selection and policy decisions without inventing historical values."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "b8c9d0e1f2a3"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("scans", sa.Column("prediction_context", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("scans", "prediction_context")
