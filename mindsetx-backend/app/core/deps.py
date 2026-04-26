"""
deps.py — FastAPI dependency injection for authentication.

Provides:
  get_current_user  — validates access token, returns active User object
  get_current_user_optional — same but returns None for unauthenticated requests (public routes)
"""

import uuid
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import decode_access_token, TokenExpiredError, TokenInvalidError
from app.database import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

# auto_error=False lets us handle the error ourselves for better messages
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Validates the Bearer access token and returns the authenticated User.

    Error mapping:
      No token         → 401 (with WWW-Authenticate header)
      Expired token    → 401 with specific message to trigger client refresh
      Invalid token    → 401
      User not found   → 401 (don't reveal whether account exists)
      User deactivated → 403
    """
    # ── Step 1: Token present? ────────────────────────────────────────────────
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please include a Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # ── Step 2: Decode and validate ───────────────────────────────────────────
    try:
        user_id_str = decode_access_token(token)
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session has expired. Please log in again.",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        )
    except TokenInvalidError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ── Step 3: Parse UUID ────────────────────────────────────────────────────
    try:
        user_id = uuid.UUID(user_id_str)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed authentication token.",
        )

    # ── Step 4: Fetch user from DB ────────────────────────────────────────────
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        # Log for monitoring (no PII — just the event)
        logger.warning("Token contained valid UUID but user not found in DB.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",  # Don't reveal user doesn't exist
        )

    # ── Step 5: Account active check ─────────────────────────────────────────
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact support.",
        )

    return user


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    Same as get_current_user but returns None instead of raising 401.
    Use this for routes that work for both authenticated and anonymous users.
    """
    if not credentials or not credentials.credentials:
        return None
    try:
        return await get_current_user(credentials=credentials, db=db)
    except HTTPException:
        return None
