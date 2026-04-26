"""Initial schema: users, journal_entries, mood_logs, streaks

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-04-26
"""
from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(120), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_email_active", "users", ["email", "is_active"])

    # ── journal_entries ───────────────────────────────────────────────────────
    op.create_table(
        "journal_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("distortion_pattern", sa.String(120), nullable=True),
        sa.Column("reframed_thought", sa.Text(), nullable=True),
        sa.Column("suggested_action", sa.Text(), nullable=True),
        sa.Column("ai_processed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_je_user_created", "journal_entries", ["user_id", "created_at"])
    op.create_index("ix_je_distortion", "journal_entries", ["distortion_pattern"])

    # ── mood_logs ─────────────────────────────────────────────────────────────
    op.create_table(
        "mood_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mood_score", sa.SmallInteger(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "log_date", name="uq_mood_user_date"),
        sa.CheckConstraint("mood_score >= 1 AND mood_score <= 4", name="ck_mood_score_range"),
    )
    op.create_index("ix_mood_user_date", "mood_logs", ["user_id", "log_date"])

    # ── streaks ───────────────────────────────────────────────────────────────
    op.create_table(
        "streaks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("current_streak", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("longest_streak", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("total_check_ins", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_active_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", name="uq_streak_user"),
        sa.CheckConstraint("current_streak >= 0", name="ck_current_streak_non_negative"),
        sa.CheckConstraint("longest_streak >= 0", name="ck_longest_streak_non_negative"),
        sa.CheckConstraint("total_check_ins >= 0", name="ck_total_check_ins_non_negative"),
        sa.CheckConstraint("longest_streak >= current_streak", name="ck_longest_gte_current"),
    )


def downgrade() -> None:
    op.drop_table("streaks")
    op.drop_table("mood_logs")
    op.drop_table("journal_entries")
    op.drop_table("users")
