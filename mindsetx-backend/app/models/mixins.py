"""
mixins.py — Reusable SQLAlchemy column mixins.

Using mixins keeps models DRY and gives us a single place
to change timestamp behaviour across the entire schema.
"""

from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """
    Adds created_at and updated_at columns to any model.
    - created_at: set once by the DB on INSERT (server_default)
    - updated_at: automatically refreshed by the DB on every UPDATE (onupdate)
    Both are timezone-aware (stored as TIMESTAMPTZ in Postgres).
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
