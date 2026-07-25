"""Add missions and operations tables

Revision ID: a1b2c3d4e5f6
Revises: c8f48b42444c
Create Date: 2026-07-26 00:00:00.000000

Adds the missions and operations tables that back the new intelligence layer.
The existing tasks table is untouched (backward compatible).

Hierarchy:
  objectives (1) ──> missions (many) ──> operations (many)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "c8f48b42444c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missions and operations tables."""

    # ── objectives ──────────────────────────────────────────────────────────
    op.create_table(
        "objectives",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("chat_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("domain", sa.String(length=50), nullable=False),
        sa.Column("domain_label", sa.String(length=100), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["chat_id"], ["chats.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_objectives_user_id", "objectives", ["user_id"])

    # ── missions ─────────────────────────────────────────────────────────────
    op.create_table(
        "missions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("objective_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["objective_id"], ["objectives.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_missions_objective_id", "missions", ["objective_id"])

    # ── operations ───────────────────────────────────────────────────────────
    op.create_table(
        "operations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("mission_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("artifact_type", sa.String(length=50), nullable=False, server_default="none"),
        sa.Column("artifact_content", sa.Text(), nullable=True),
        sa.Column("why_this", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["mission_id"], ["missions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_operations_mission_id", "operations", ["mission_id"])


def downgrade() -> None:
    """Remove missions and operations tables."""
    op.drop_index("ix_operations_mission_id", table_name="operations")
    op.drop_table("operations")
    op.drop_index("ix_missions_objective_id", table_name="missions")
    op.drop_table("missions")
    op.drop_index("ix_objectives_user_id", table_name="objectives")
    op.drop_table("objectives")
