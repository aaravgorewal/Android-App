"""
journal.py — Journal entry model

Schema: journal_entries
──────────────────────────────────────────────────────────────────
Column               Type           Constraints
──────────────────────────────────────────────────────────────────
id                   UUID           PK, default uuid4
user_id              UUID           FK → users.id, NOT NULL, INDEX
content              TEXT           NOT NULL  (sensitive — never log)
distortion_pattern   VARCHAR(120)   NULLABLE  (from AI)
reframed_thought     TEXT           NULLABLE  (from AI)
suggested_action     TEXT           NULLABLE  (from AI)
ai_processed         BOOLEAN        DEFAULT FALSE
created_at           TIMESTAMPTZ    server_default now(), INDEX
updated_at           TIMESTAMPTZ    server_default now(), onupdate
──────────────────────────────────────────────────────────────────

Indexes:
  ix_je_user_id         → fast "get all entries for user"
  ix_je_user_created    → composite for paginated journal feed
  ix_je_distortion      → enables future analytics ("most common distortion")

Scalability note:
  TEXT columns for user content — Postgres handles up to 1GB per TEXT cell.
  Do NOT use VARCHAR with a limit on user-facing text inputs.
"""

import uuid
from sqlalchemy import String, Text, Boolean, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base
from app.models.mixins import TimestampMixin


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    # ── Primary Key ───────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Foreign Key ───────────────────────────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Cascade delete — if user deleted, all entries go with them",
    )

    # ── User Content (SENSITIVE) ──────────────────────────────────────────────
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Raw thought text. NEVER log this field.",
    )

    # ── AI Reframe Output ─────────────────────────────────────────────────────
    distortion_pattern: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        comment="CBT distortion label returned by AI (e.g. Catastrophizing)",
    )
    reframed_thought: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="AI-generated CBT reframe of the user's thought",
    )
    suggested_action: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Concrete micro-action recommended by AI",
    )
    ai_processed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="FALSE until AI reframe is successfully returned and stored",
    )

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at = TimestampMixin.created_at
    updated_at = TimestampMixin.updated_at

    # ── Relationship ──────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship(  # noqa: F821
        "User",
        back_populates="journal_entries",
        lazy="noload",   # Don't load user object when fetching entries
    )

    # ── Indexes ───────────────────────────────────────────────────────────────
    __table_args__ = (
        # Primary query: "give me this user's journal, newest first"
        Index("ix_je_user_created", "user_id", "created_at"),
        # Analytics: "which distortions are most common" (future dashboard)
        Index("ix_je_distortion", "distortion_pattern"),
    )

    def __repr__(self) -> str:
        return f"<JournalEntry id={self.id} user_id={self.user_id} processed={self.ai_processed}>"

    @property
    def has_reframe(self) -> bool:
        """Quick check if AI reframe has been populated."""
        return self.ai_processed and self.reframed_thought is not None
