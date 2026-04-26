"""
mood.py — Daily mood log model

Schema: mood_logs
──────────────────────────────────────────────────────────────────
Column        Type           Constraints
──────────────────────────────────────────────────────────────────
id            UUID           PK, default uuid4
user_id       UUID           FK → users.id, NOT NULL
mood_score    SMALLINT       NOT NULL, CHECK (1–4)
note          TEXT           NULLABLE (optional free-text)
log_date      DATE           NOT NULL
created_at    TIMESTAMPTZ    server_default now()
updated_at    TIMESTAMPTZ    server_default now(), onupdate
──────────────────────────────────────────────────────────────────

Constraints:
  uq_mood_user_date     → prevents >1 mood log per user per day (enforced by DB)
  ck_mood_score_range   → DB-level check: score must be 1, 2, 3, or 4

Indexes:
  ix_mood_user_date     → composite for fetching weekly trend

Scalability note:
  SMALLINT saves 2 bytes vs INTEGER per row — mood_logs will be a
  high-volume table (1 row/user/day), so column sizing matters at scale.
"""

import uuid
from datetime import date
from sqlalchemy import SmallInteger, Date, Text, Index, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base
from app.models.mixins import TimestampMixin

# Human-readable label map (for serialization / display)
MOOD_LABELS: dict[int, str] = {
    1: "Down",
    2: "Okay",
    3: "Good",
    4: "Great",
}

MOOD_EMOJIS: dict[int, str] = {
    1: "😞",
    2: "😐",
    3: "🙂",
    4: "😄",
}


class MoodLog(Base):
    __tablename__ = "mood_logs"

    # ── Primary Key ───────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Foreign Key ───────────────────────────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── Mood Data ─────────────────────────────────────────────────────────────
    mood_score: Mapped[int] = mapped_column(
        SmallInteger,     # 2 bytes — saves space on high-volume table
        nullable=False,
        comment="1=Down, 2=Okay, 3=Good, 4=Great",
    )
    note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional free-text note with the mood (future feature)",
    )
    log_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Calendar date of the mood log (timezone-naive — user's local date)",
    )

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at = TimestampMixin.created_at
    updated_at = TimestampMixin.updated_at

    # ── Relationship ──────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship(  # noqa: F821
        "User",
        back_populates="mood_logs",
        lazy="noload",
    )

    # ── Table Constraints & Indexes ───────────────────────────────────────────
    __table_args__ = (
        # Prevent duplicate daily log — DB enforces this, not just the app layer
        UniqueConstraint("user_id", "log_date", name="uq_mood_user_date"),
        # Score must be 1–4 at DB level
        CheckConstraint("mood_score >= 1 AND mood_score <= 4", name="ck_mood_score_range"),
        # Primary query pattern: weekly trend for a user
        Index("ix_mood_user_date", "user_id", "log_date"),
    )

    def __repr__(self) -> str:
        return f"<MoodLog user_id={self.user_id} date={self.log_date} score={self.mood_score}>"

    @property
    def label(self) -> str:
        return MOOD_LABELS.get(self.mood_score, "Unknown")

    @property
    def emoji(self) -> str:
        return MOOD_EMOJIS.get(self.mood_score, "❓")
