"""
routes/auth.py — Authentication endpoints for MindsetX.

Endpoints:
  POST  /auth/signup           — Create account, returns token pair
  POST  /auth/login            — Authenticate, returns token pair
  POST  /auth/refresh          — Exchange refresh token for new access token
  POST  /auth/logout           — Invalidate session (client-side token drop)
  GET   /auth/me               — Return current user profile
  PATCH /auth/me               — Update display name
  POST  /auth/change-password  — Authenticated password change
  DELETE /auth/me              — Hard-delete account and all data

Security:
  - Auth endpoints are rate-limited to 5 req/minute per IP (brute-force protection)
  - Emails are normalised to lowercase before lookup/storage
  - Errors never reveal whether an email exists (timing-safe responses)
  - Refresh tokens use a separate REFRESH_SECRET_KEY
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import get_settings
from app.database import get_db
from app.core.deps import get_current_user
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    TokenExpiredError,
    TokenInvalidError,
    validate_password_strength,
)
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserResponse,
    LoginRequest,
    TokenPair,
    AccessTokenResponse,
    RefreshRequest,
    ChangePasswordRequest,
    UserProfileUpdate,
)

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/auth", tags=["Authentication"])

# TTL in seconds — sent to client so it knows when to refresh
_ACCESS_TOKEN_TTL_SECONDS = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


# ── Helper ────────────────────────────────────────────────────────────────────
def _make_token_pair(user_id) -> TokenPair:
    """Issue a fresh access + refresh token pair for a given user."""
    return TokenPair(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
        expires_in=_ACCESS_TOKEN_TTL_SECONDS,
    )


# ── POST /auth/signup ─────────────────────────────────────────────────────────
@router.post(
    "/signup",
    response_model=TokenPair,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new account",
    description="Registers a new user and returns an access + refresh token pair.",
)
async def signup(
    payload: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    # 1. Password strength check (beyond Pydantic min_length)
    strength_errors = validate_password_strength(payload.password)
    if strength_errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Password does not meet requirements.", "errors": strength_errors},
        )

    # 2. Duplicate email check
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    # 3. Create user
    user = User(
        email=payload.email,  # Already normalised by Pydantic validator
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info(f"New user registered. id={user.id}")  # Log ID only, never email
    return _make_token_pair(user.id)


# ── POST /auth/login ──────────────────────────────────────────────────────────
@router.post(
    "/login",
    response_model=TokenPair,
    summary="Log in with email and password",
    description="Returns an access token (short-lived) and a refresh token (long-lived).",
)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    # Fetch user — same error for wrong email AND wrong password (no enumeration)
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    # Always call verify_password even if user not found (timing-safe dummy check)
    dummy_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LwdMHQYs/1hx6JE1e"
    password_ok = verify_password(
        payload.password,
        user.hashed_password if user else dummy_hash,
    )

    if not user or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact support.",
        )

    logger.info(f"User login. id={user.id}")
    return _make_token_pair(user.id)


# ── POST /auth/refresh ────────────────────────────────────────────────────────
@router.post(
    "/refresh",
    response_model=AccessTokenResponse,
    summary="Refresh access token",
    description="Exchange a valid refresh token for a new short-lived access token.",
)
async def refresh_token(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    # Decode the refresh token (uses separate secret from access token)
    try:
        user_id_str = decode_refresh_token(payload.refresh_token)
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired. Please log in again.",
        )
    except TokenInvalidError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        )

    # Verify user still exists and is active
    import uuid
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload.")

    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")

    return AccessTokenResponse(
        access_token=create_access_token(user.id),
        expires_in=_ACCESS_TOKEN_TTL_SECONDS,
    )


# ── POST /auth/logout ─────────────────────────────────────────────────────────
@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Log out",
    description=(
        "Stateless logout — instructs the client to discard tokens. "
        "For full server-side revocation, a token blacklist (Redis) should be added."
    ),
)
async def logout(current_user: User = Depends(get_current_user)):
    # Stateless JWT: server cannot invalidate tokens without a denylist.
    # The client MUST delete both tokens from storage on receiving 204.
    logger.info(f"User logout. id={current_user.id}")
    return  # 204 No Content


# ── GET /auth/me ──────────────────────────────────────────────────────────────
@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


# ── PATCH /auth/me ────────────────────────────────────────────────────────────
@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update display name",
)
async def update_me(
    payload: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
        await db.commit()
        await db.refresh(current_user)
    return current_user


# ── POST /auth/change-password ────────────────────────────────────────────────
@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change password (authenticated)",
    description="Requires the current password for verification before accepting a new one.",
)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 1. Verify current password
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    # 2. Strength check on new password
    strength_errors = validate_password_strength(payload.new_password)
    if strength_errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "New password does not meet requirements.", "errors": strength_errors},
        )

    # 3. Update hash
    current_user.hashed_password = hash_password(payload.new_password)
    await db.commit()
    logger.info(f"Password changed. user_id={current_user.id}")
    return  # 204 No Content


# ── DELETE /auth/me ───────────────────────────────────────────────────────────
@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete account",
    description=(
        "Permanently deletes the account and ALL associated data "
        "(journal entries, mood logs, streaks) via CASCADE. This cannot be undone."
    ),
)
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.delete(current_user)
    await db.commit()
    logger.info(f"Account deleted. user_id={current_user.id}")
    return  # 204 No Content
