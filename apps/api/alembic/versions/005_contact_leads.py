"""Contact leads table

Revision ID: 005
Revises: 004
Create Date: 2026-10-28
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "contact_leads",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("company", sa.String(255), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("locale", sa.String(8), nullable=False, server_default="en"),
        sa.Column("source", sa.String(64), nullable=False, server_default="enterprise_form"),
        sa.Column("status", sa.String(32), nullable=False, server_default="NEW"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_contact_leads_email", "contact_leads", ["email"])
    op.create_index("ix_contact_leads_status", "contact_leads", ["status"])


def downgrade() -> None:
    op.drop_table("contact_leads")
