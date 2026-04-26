"""
streak.py — User streak tracking model

Schema: streaks
──────────────────────────────────────────────────────────────────
Column              Type           Constraints
──────────────────────────────────────────────────────────────────
id                  UUID           PK, default uuid4
user_id             UUID           FK → users.id, UNIQUE, NOT NULL
current_streak      SMALLINT       DEFAULT 0, CHECK >= 0
longest_streak      SMALLINT       DEFAULT 0, CHECK >= 0
last_active_date    DATE           NULLABLE
total_check_ins     INTEGER        DEFAULT 0
created_at          TIMESTAMPTZ    server_default now()
updated_at          TIMESTAMPTZ    server_default now(), onupdate
──────────────────────────────────────────────────────────────────

Design decisions:
  - One row per user (UNIQUE on user_id) — no history table needed at MVP
  - total_check_ins is a running counter (increment-only) for lifetime stats
  - last_active_date drives streak calculation in the service layer
  - SMALLINT for streak counters — a streak of 32,767 is more than enough
  - CHECK constraints ensure counters never go negative (data corruption guard)

Scalability note:
  If we later want "streak history" (e.g., "you broke a 30-day streak on X"),
  add a streak_history table without touching this model.
"""

import uuid
from datetime import date
from sqlalchemy import SmallInteger, Integer, Date, Index, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base
from app.models.mixins import TimestampMixin


class Streak(Base):
    __tablename__ = "streaks"

    # ── Primary Key ───────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Foreign Key (unique — one row per user) ───────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="One streak record per user",
    )

    # ── Streak Counters ───────────────────────────────────────────────────────
    current_streak: Mapped[int] = mapped_column(
        SmallInteger,
        default=0,
        nullable=False,
        comment="Consecutive days active (resets to 0 if a day is missed)",
    )
    longest_streak: Mapped[int] = mapped_column(
        SmallInteger,
        default=0,
        nullable=False,
        comment="Historical best streak — never decreases",
    )
    total_check_ins: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Lifetime total days the user checked in (increment-only counter)",
    )

    # ── Activity Tracking ─────────────────────────────────────────────────────
    last_active_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="The last calendar date the user completed a check-in (mood + journal)",
    )

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at = TimestampMixin.created_at
    updated_at = TimestampMixin.updated_at

    # ── Relationship ──────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship(  # noqa: F821
        "User",
        back_populates="streak",
        lazy="noload",
    )

    # ── Table Constraints & Indexes ───────────────────────────────────────────
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_streak_user"),
        CheckConstraint("current_streak >= 0", name="ck_current_streak_non_negative"),
        CheckConstraint("longest_streak >= 0", name="ck_longest_streak_non_negative"),
        CheckConstraint("total_check_ins >= 0", name="ck_total_check_ins_non_negative"),
        CheckConstraint("longest_streak >= current_streak", name="ck_longest_gte_current"),
    )

    def __repr__(self) -> str:
        return (
            f"<Streak user_id={self.user_id} "
            f"current={self.current_streak} "
            f"longest={self.longest_streak} "
            f"total={self.total_check_ins}>"
        )

    @property
    def is_active_today(self) -> bool:
        """Returns True if the user has already checked in today."""
        from datetime import datetime, timezone
        return self.last_active_date == datetime.now(timezone.utc).date()
