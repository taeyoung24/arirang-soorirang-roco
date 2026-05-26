"""create recent learning records

Revision ID: 9b2d7f6a4c31
Revises: 7b8c2d4f1a90
Create Date: 2026-05-23 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "9b2d7f6a4c31"
down_revision = "7b8c2d4f1a90"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "recent_learning_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("card_id", sa.String(), nullable=False),
        sa.Column("last_viewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["card_id"], ["quizzes.card_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("card_id"),
    )
    op.create_index(
        op.f("ix_recent_learning_records_last_viewed_at"),
        "recent_learning_records",
        ["last_viewed_at"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_recent_learning_records_last_viewed_at"),
        table_name="recent_learning_records",
    )
    op.drop_table("recent_learning_records")
