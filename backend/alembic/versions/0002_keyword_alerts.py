"""add keyword alerts"""
from alembic import op
import sqlalchemy as sa

revision = "0002_keyword_alerts"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "keyword_alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("keyword", sa.String(length=120), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("keyword_alerts")
