from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.journal import JournalCreate, JournalResponse, ReframeRequest, ReframeResponse
from app.services import journal_service
from app.services.ai_service import reframe_thought

router = APIRouter(prefix="/journal", tags=["Journal"])


@router.post(
    "/",
    response_model=JournalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save a thought and get an AI CBT reframe",
)
async def create_journal(
    payload: JournalCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Full pipeline:
    1. Saves the journal entry
    2. Runs CBT-based AI reframe
    3. Stores the reframe result
    4. Updates the daily streak
    """
    try:
        entry = await journal_service.create_journal_entry(db, current_user.id, payload)
        return entry
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Your entry was not saved.",
        )


@router.post(
    "/reframe",
    response_model=ReframeResponse,
    summary="Get a CBT reframe without saving (preview mode)",
)
async def reframe_only(
    payload: ReframeRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Runs the AI CBT analysis on-demand without persisting.
    Use this for live previews before the user commits to saving.
    """
    try:
        return await reframe_thought(payload.content)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/",
    response_model=list[JournalResponse],
    summary="Get recent journal entries (last 20)",
)
async def get_entries(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await journal_service.get_user_entries(db, current_user.id)
