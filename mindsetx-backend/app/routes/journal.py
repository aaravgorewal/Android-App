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
    summary="Save a thought and get AI reframe",
)
async def create_journal(
    payload: JournalCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Saves the user's journal entry to the database, triggers AI reframing,
    stores the result, and updates the daily streak.
    """
    try:
        entry = await journal_service.create_journal_entry(db, current_user.id, payload)
        return entry
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service temporarily unavailable. Your entry was not saved.",
        )


@router.post(
    "/reframe",
    response_model=ReframeResponse,
    summary="Reframe a thought via AI (without saving)",
)
async def reframe_only(
    payload: ReframeRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Runs AI reframing on-demand without persisting to the database.
    Useful for previewing reframes before committing.
    """
    try:
        return await reframe_thought(payload.content)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is currently unavailable. Please try again later.",
        )


@router.get(
    "/",
    response_model=list[JournalResponse],
    summary="Get recent journal entries",
)
async def get_entries(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await journal_service.get_user_entries(db, current_user.id)
