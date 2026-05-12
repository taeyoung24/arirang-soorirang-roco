"""add tts urls and quiz sentence link

Revision ID: 7b8c2d4f1a90
Revises: 42116df0ca1f
Create Date: 2026-05-12 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "7b8c2d4f1a90"
down_revision = "42116df0ca1f"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("sentences", sa.Column("tts_url", sa.String(), nullable=True))
    op.add_column("quizzes", sa.Column("sentence_id", sa.String(), nullable=True))
    op.add_column("quizzes", sa.Column("tts_url", sa.String(), nullable=True))
    op.create_index(
        op.f("ix_quizzes_sentence_id"),
        "quizzes",
        ["sentence_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_quizzes_sentence_id_sentences",
        "quizzes",
        "sentences",
        ["sentence_id"],
        ["sentence_id"],
    )


def downgrade():
    op.drop_constraint("fk_quizzes_sentence_id_sentences", "quizzes", type_="foreignkey")
    op.drop_index(op.f("ix_quizzes_sentence_id"), table_name="quizzes")
    op.drop_column("quizzes", "tts_url")
    op.drop_column("quizzes", "sentence_id")
    op.drop_column("sentences", "tts_url")
