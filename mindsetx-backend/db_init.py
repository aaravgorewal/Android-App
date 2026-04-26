"""
db_init.py — Standalone script to initialize the database.

USE THIS ONLY IN DEVELOPMENT.
In production, use Alembic migrations:
  alembic upgrade head

Run from mindsetx-backend root:
  python db_init.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base

# Import all models so their tables are registered in metadata
import app.models  # noqa: F401


async def init_db() -> None:
    print("Connecting to PostgreSQL...")
    async with engine.begin() as conn:
        print("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("✅ All tables created successfully.")
        print("\nTables in database:")
        tables = list(Base.metadata.tables.keys())
        for t in sorted(tables):
            print(f"  - {t}")
    await engine.dispose()
    print("\nDone. You can now run: python run.py")


if __name__ == "__main__":
    asyncio.run(init_db())
