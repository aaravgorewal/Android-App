"""
user.py — User model

Schema: users
─────────────────────────────────────────────────────
Column            Type           Constraints
─────────────────────────────────────────────────────
id                UUID           PK, default uuid4
email             VARCHAR(255)   UNIQUE, NOT NULL, INDEX
hashed_password   VARCHAR(255)   NOT NULL
full_name         VARCHAR(120)   NULLABLE
is_active         BOOLEAN        DEFAULT TRUE
created_at        TIMESTAMPTZ    server_default now()
updated_at        TIMESTAMPTZ    server_default now(), onupdate now()
─────────────────────────────────────────────────────

Relationships:
  journal_entries → JournalEntry (one-to-many, cascade delete)
  mood_logs       → MoodLog      (one-to-many, cascade delete)
  streak          → Streak       (one-to-one,  cascade delete)
"""

import uuid
from sqlalchemy import String, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base
from app.models.mixins import TimestampMixin


class User(Base):
    __tablename__ = "users"

    # ── Primary Key ───────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="UUID primary key — avoids sequential ID enumeration attacks",
    )

    # ── Identity ──────────────────────────────────────────────────────────────
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Lowercase email, unique across all users",
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="bcrypt hash — raw password is never stored",
    )
    full_name: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    # ── Account State ─────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Soft deactivation — data preserved, login denied",
    )

    # ── Timestamps (via mixin) ────────────────────────────────────────────────
    created_at = TimestampMixin.created_at
    updated_at = TimestampMixin.updated_at

    # ── Relationships ─────────────────────────────────────────────────────────
    journal_entries: Mapped[list["JournalEntry"]] = relationship(  # noqa: F821
        "JournalEntry",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,   # DB-level CASCADE handles deletes (faster)
        lazy="noload",          # Never eager-load journal entries on user fetch
    )
    mood_logs: Mapped[list["MoodLog"]] = relationship(  # noqa: F821
        "MoodLog",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="noload",
    )
    streak: Mapped["Streak | None"] = relationship(  # noqa: F821
        "Streak",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",        # Always load streak with user (small, frequently needed)
    )

    # ── Explicit Indexes ──────────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_users_email_active", "email", "is_active"),  # Auth lookup
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} active={self.is_active}>"
