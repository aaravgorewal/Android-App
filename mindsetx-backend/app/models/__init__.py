"""
models/__init__.py

Import all models here so SQLAlchemy's metadata is fully populated
before create_all() or Alembic autogenerate runs.
The import ORDER matters — User must be imported before models that
reference it via ForeignKey, to avoid forward-reference resolution errors.
"""

from app.models.user import User  # noqa: F401  (base table, no FK deps)
from app.models.journal import JournalEntry  # noqa: F401  (depends on users)
from app.models.mood import MoodLog  # noqa: F401  (depends on users)
from app.models.streak import Streak  # noqa: F401  (depends on users)

__all__ = ["User", "JournalEntry", "MoodLog", "Streak"]
