import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.journal import JournalEntry
from app.models.streak import Streak
from app.schemas.journal import JournalCreate
from app.services.ai_service import reframe_thought


async def create_journal_entry(
    db: AsyncSession,
    user_id: uuid.UUID,
    data: JournalCreate,
) -> JournalEntry:
    """Save a thought, trigger AI reframe, store result, update streak."""

    # 1. Get AI reframe
    reframe = await reframe_thought(data.content)

    # 2. Save journal entry with reframe data
    entry = JournalEntry(
        user_id=user_id,
        content=data.content,
        distortion_pattern=reframe.pattern,
        reframed_thought=reframe.reframe,
        suggested_action=reframe.action,
    )
    db.add(entry)

    # 3. Update streak
    await _update_streak(db, user_id)

    await db.commit()
    await db.refresh(entry)
    return entry


async def get_user_entries(
    db: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 20,
) -> list[JournalEntry]:
    result = await db.execute(
        select(JournalEntry)
        .where(JournalEntry.user_id == user_id)
        .order_by(JournalEntry.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


async def _update_streak(db: AsyncSession, user_id: uuid.UUID) -> None:
    today = datetime.now(timezone.utc).date()

    result = await db.execute(select(Streak).where(Streak.user_id == user_id))
    streak = result.scalar_one_or_none()

    if not streak:
        streak = Streak(user_id=user_id, current_streak=1, longest_streak=1, last_active_date=today)
        db.add(streak)
        return

    if streak.last_active_date == today:
        return  # Already logged today, no update needed

    yesterday = (datetime.now(timezone.utc).date().toordinal() - 1)
    last_ordinal = streak.last_active_date.toordinal() if streak.last_active_date else 0

    if last_ordinal == yesterday:
        streak.current_streak += 1
    else:
        streak.current_streak = 1  # Streak broken

    streak.longest_streak = max(streak.longest_streak, streak.current_streak)
    streak.last_active_date = today
