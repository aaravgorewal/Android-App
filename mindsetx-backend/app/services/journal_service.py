"""
journal_service.py — Business logic for journal entries and streak updates.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.journal import JournalEntry
from app.models.streak import Streak
from app.schemas.journal import JournalCreate
from app.services.ai_service import reframe_thought


async def create_journal_entry(
    db: AsyncSession,
    user_id: uuid.UUID,
    data: JournalCreate,
) -> JournalEntry:
    """
    Full pipeline:
    1. Call AI to get CBT reframe
    2. Persist journal entry (with reframe data + ai_processed=True)
    3. Update streak and total_check_ins
    4. Commit all changes atomically
    """
    # 1. AI reframe — do this BEFORE writing to DB so we can mark ai_processed correctly
    reframe = await reframe_thought(data.content)

    # 2. Build entry
    entry = JournalEntry(
        user_id=user_id,
        content=data.content,
        distortion_pattern=reframe.pattern,
        reframed_thought=reframe.reframe,
        suggested_action=reframe.action,
        ai_processed=True,
    )
    db.add(entry)

    # 3. Update streak (within same transaction)
    await _update_streak(db, user_id)

    # 4. Commit atomically — if any step fails, nothing is written
    await db.commit()
    await db.refresh(entry)
    return entry


async def get_user_entries(
    db: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 20,
    offset: int = 0,
) -> list[JournalEntry]:
    """Returns paginated journal entries for a user, newest first."""
    result = await db.execute(
        select(JournalEntry)
        .where(JournalEntry.user_id == user_id)
        .order_by(JournalEntry.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def _update_streak(db: AsyncSession, user_id: uuid.UUID) -> None:
    """
    Streak logic:
    - If user has no streak row → create one (current=1, total=1)
    - If last_active_date == today → already checked in, skip
    - If last_active_date == yesterday → increment streak (consecutive day)
    - Otherwise → streak broken, reset to 1
    Always increments total_check_ins.
    longest_streak is updated if current exceeds it.
    """
    today = datetime.now(timezone.utc).date()

    result = await db.execute(select(Streak).where(Streak.user_id == user_id))
    streak = result.scalar_one_or_none()

    if not streak:
        db.add(Streak(
            user_id=user_id,
            current_streak=1,
            longest_streak=1,
            total_check_ins=1,
            last_active_date=today,
        ))
        return

    # Already checked in today — don't double-count
    if streak.last_active_date == today:
        return

    # Determine streak continuation
    if streak.last_active_date is not None:
        delta = today.toordinal() - streak.last_active_date.toordinal()
        if delta == 1:
            streak.current_streak += 1   # Consecutive
        else:
            streak.current_streak = 1    # Gap — reset

    streak.longest_streak = max(streak.longest_streak, streak.current_streak)
    streak.total_check_ins += 1
    streak.last_active_date = today
