import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.mood import MoodLog
from app.models.streak import Streak
from app.models.journal import JournalEntry
from app.schemas.progress import ProgressResponse, MoodEntry, MoodCreate


async def log_mood(db: AsyncSession, user_id: uuid.UUID, data: MoodCreate) -> MoodLog:
    log_date = data.log_date or datetime.now(timezone.utc).date()

    # Upsert: replace today's mood if already logged
    result = await db.execute(
        select(MoodLog).where(MoodLog.user_id == user_id, MoodLog.log_date == log_date)
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.mood_score = data.mood_score
        await db.commit()
        await db.refresh(existing)
        return existing

    mood = MoodLog(user_id=user_id, mood_score=data.mood_score, log_date=log_date)
    db.add(mood)
    await db.commit()
    await db.refresh(mood)
    return mood


async def get_progress(db: AsyncSession, user_id: uuid.UUID) -> ProgressResponse:
    # --- Streak ---
    streak_result = await db.execute(select(Streak).where(Streak.user_id == user_id))
    streak = streak_result.scalar_one_or_none()

    current_streak = streak.current_streak if streak else 0
    longest_streak = streak.longest_streak if streak else 0

    # --- Weekly moods (last 7 days) ---
    today = datetime.now(timezone.utc).date()
    week_ago = today - timedelta(days=6)

    mood_result = await db.execute(
        select(MoodLog)
        .where(MoodLog.user_id == user_id, MoodLog.log_date >= week_ago)
        .order_by(MoodLog.log_date.asc())
    )
    mood_logs = mood_result.scalars().all()
    weekly_moods = [MoodEntry(date=log.log_date, mood_score=log.mood_score) for log in mood_logs]

    # --- Total journal entries ---
    total_result = await db.execute(
        select(func.count(JournalEntry.id)).where(JournalEntry.user_id == user_id)
    )
    total_entries = total_result.scalar_one() or 0

    # --- Insight ---
    insight = _generate_insight(weekly_moods, total_entries)

    return ProgressResponse(
        current_streak=current_streak,
        longest_streak=longest_streak,
        weekly_moods=weekly_moods,
        total_entries=total_entries,
        insight=insight,
    )


def _generate_insight(moods: list[MoodEntry], entries: int) -> str | None:
    if not moods:
        return "Start by logging your mood and journaling today."
    if len(moods) >= 3:
        scores = [m.mood_score for m in moods]
        avg = sum(scores) / len(scores)
        if avg >= 3:
            return "You've been feeling positive this week. Keep it up!"
        elif avg <= 2:
            return "It's been a tough week — journaling today can help you process it."
    if entries > 5:
        return "You felt better on days you journaled. Consistency is building."
    return None
