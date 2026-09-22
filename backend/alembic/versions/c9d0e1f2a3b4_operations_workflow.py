"""Account controls, audit trail and versioned content proposals."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "c9d0e1f2a3b4"
down_revision = "b8c9d0e1f2a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("status", sa.String(20), nullable=False, server_default="active"))
    op.create_check_constraint("ck_users_status", "users", "status IN ('active', 'suspended')")
    op.create_check_constraint("ck_users_token_version", "users", "token_version >= 0")
    op.add_column("disease_info", sa.Column("content_version", sa.Integer(), nullable=False, server_default="1"))
    op.create_check_constraint("ck_disease_info_content_version", "disease_info", "content_version >= 1")
    op.create_table(
        "audit_events",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", sa.String(100), nullable=False),
        sa.Column("outcome", sa.String(20), nullable=False, server_default="success"),
        sa.Column("metadata", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_audit_created_at", "audit_events", ["created_at"])
    op.create_index("idx_audit_resource", "audit_events", ["resource_type", "resource_id", "created_at"])
    op.create_table(
        "disease_proposals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("proposer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("label_key", sa.String(50), nullable=False),
        sa.Column("proposal_type", sa.String(30), nullable=False, server_default="update_content"),
        sa.Column("base_content_version", sa.Integer(), nullable=False),
        sa.Column("disease_name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("treatment", sa.Text()),
        sa.Column("severity_level", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("reviewer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("review_note", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("proposal_type = 'update_content'", name="ck_proposals_type"),
        sa.CheckConstraint("base_content_version >= 1", name="ck_proposals_version"),
        sa.CheckConstraint("status IN ('pending', 'approved', 'rejected')", name="ck_proposals_status"),
        sa.CheckConstraint("severity_level IN ('low', 'medium', 'high')", name="ck_proposals_severity"),
        sa.CheckConstraint("(status = 'pending' AND reviewed_at IS NULL AND reviewer_id IS NULL) OR (status <> 'pending' AND reviewed_at IS NOT NULL)", name="ck_proposals_review"),
        sa.CheckConstraint("status <> 'rejected' OR (review_note IS NOT NULL AND length(trim(review_note)) > 0)", name="ck_proposals_reject_note"),
    )
    op.create_index("idx_proposals_mine", "disease_proposals", ["proposer_id", "created_at", "id"])
    op.create_index("idx_proposals_queue", "disease_proposals", ["status", "created_at", "id"])


def downgrade() -> None:
    op.drop_table("disease_proposals")
    op.drop_table("audit_events")
    op.drop_constraint("ck_disease_info_content_version", "disease_info", type_="check")
    op.drop_column("disease_info", "content_version")
    op.drop_constraint("ck_users_token_version", "users", type_="check")
    op.drop_constraint("ck_users_status", "users", type_="check")
    op.drop_column("users", "status")
