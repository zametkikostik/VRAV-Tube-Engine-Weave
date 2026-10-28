"""AI usage ledger

Revision ID: 003
Revises: 002
Create Date: 2026-10-28
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_usage_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("audit_job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("model", sa.String(128), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("provider_reported_cost", sa.Numeric(12, 6), nullable=True),
        sa.Column("internal_estimated_cost", sa.Numeric(12, 6), nullable=True),
        sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
        sa.Column("request_outcome", sa.String(32), nullable=False, server_default="success"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_usage_records_tenant_id", "ai_usage_records", ["tenant_id"])
    op.create_index("ix_ai_usage_records_organization_id", "ai_usage_records", ["organization_id"])
    op.create_index("ix_ai_usage_records_created_at", "ai_usage_records", ["created_at"])


def downgrade() -> None:
    op.drop_table("ai_usage_records")
