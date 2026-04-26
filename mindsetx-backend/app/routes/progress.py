from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.progress import ProgressResponse, MoodCreate, MoodEntry
from app.services import progress_service

router = APIRouter(prefix="/progress", tags=["Progress"])


@router.get(
    "/",
    response_model=ProgressResponse,
    summary="Get user's mood trends, streak, and insights",
)
async def get_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await progress_service.get_progress(db, current_user.id)


@router.post(
    "/mood",
    response_model=MoodEntry,
    status_code=status.HTTP_201_CREATED,
    summary="Log today's mood",
)
async def log_mood(
    payload: MoodCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Logs or updates the user's mood for the day.
    Accepts 1 (Down), 2 (Okay), 3 (Good), 4 (Great).
    """
    mood_log = await progress_service.log_mood(db, current_user.id, payload)
    return MoodEntry(date=mood_log.log_date, mood_score=mood_log.mood_score)
