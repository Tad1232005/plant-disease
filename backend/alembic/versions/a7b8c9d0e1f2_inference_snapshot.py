"""Store effective inference policy without inventing historical settings.

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "a7b8c9d0e1f2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("scans", sa.Column("inference_snapshot", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("scans", "inference_snapshot")
