"""
schemas/user.py — Pydantic models for auth and user data.
"""

import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


# ── Signup ────────────────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Min 8 chars, must include uppercase, lowercase, and a number.",
    )
    full_name: str | None = Field(
        default=None,
        max_length=120,
        description="Optional display name.",
    )

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        """Store emails lowercase to prevent duplicate accounts."""
        return v.lower().strip()

    @field_validator("full_name")
    @classmethod
    def strip_name(cls, v: str | None) -> str | None:
        return v.strip() if v else None


# ── Login ─────────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.lower().strip()


# ── Token Responses ───────────────────────────────────────────────────────────
class TokenPair(BaseModel):
    """Returned on login and signup — both tokens in one response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Access token TTL in seconds (for client-side timer)


class AccessTokenResponse(BaseModel):
    """Returned on token refresh — only a new access token."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=10)


# ── Change Password ───────────────────────────────────────────────────────────
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def passwords_differ(self) -> "ChangePasswordRequest":
        if self.current_password == self.new_password:
            raise ValueError("New password must be different from the current password.")
        return self


# ── User Response ─────────────────────────────────────────────────────────────
class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)

    @field_validator("full_name")
    @classmethod
    def strip_name(cls, v: str | None) -> str | None:
        return v.strip() if v else None
