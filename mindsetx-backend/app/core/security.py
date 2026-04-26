"""
security.py — Cryptographic helpers for MindsetX auth system.

Covers:
- bcrypt password hashing (cost factor 12 — balances security vs. latency)
- JWT access tokens  (short-lived: 60 min)
- JWT refresh tokens (long-lived: 7 days, separate secret to allow rotation)
- Token type discrimination via "type" claim to prevent token confusion attacks
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional
from enum import Enum

from jose import JWTError, ExpiredSignatureError, jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()

# ── Password Hashing ──────────────────────────────────────────────────────────
# bcrypt rounds=12: ~250ms hash time — slow enough to resist brute-force,
# fast enough for normal login UX.
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Timing-safe bcrypt verification via passlib."""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(plain_password: str) -> str:
    """Returns a bcrypt hash with embedded salt. Never store the original."""
    return pwd_context.hash(plain_password)


# ── Token Types ───────────────────────────────────────────────────────────────
class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


# ── Token Claims ──────────────────────────────────────────────────────────────
_TOKEN_SECRETS: dict[TokenType, str] = {
    TokenType.ACCESS: settings.SECRET_KEY,
    TokenType.REFRESH: settings.REFRESH_SECRET_KEY,
}

_TOKEN_EXPIRY: dict[TokenType, timedelta] = {
    TokenType.ACCESS: timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    TokenType.REFRESH: timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
}


def _create_token(subject: str | uuid.UUID, token_type: TokenType) -> str:
    """
    Internal token factory.

    Payload claims:
      sub  — user UUID (string)
      type — "access" | "refresh"  (prevents using refresh token as access)
      iat  — issued at (UTC)
      exp  — expiry (UTC)
      jti  — unique token ID (for future revocation/blacklisting support)
    """
    now = datetime.now(timezone.utc)
    expire = now + _TOKEN_EXPIRY[token_type]
    payload = {
        "sub": str(subject),
        "type": token_type.value,
        "iat": now,
        "exp": expire,
        "jti": str(uuid.uuid4()),  # Unique token ID — enables per-token revocation later
    }
    return jwt.encode(payload, _TOKEN_SECRETS[token_type], algorithm=settings.ALGORITHM)


def create_access_token(subject: str | uuid.UUID) -> str:
    return _create_token(subject, TokenType.ACCESS)


def create_refresh_token(subject: str | uuid.UUID) -> str:
    return _create_token(subject, TokenType.REFRESH)


# ── Token Decoding ────────────────────────────────────────────────────────────
class TokenError(Exception):
    """Base for token validation failures — maps to specific HTTP errors."""


class TokenExpiredError(TokenError):
    pass


class TokenInvalidError(TokenError):
    pass


def _decode_token(token: str, expected_type: TokenType) -> str:
    """
    Decodes and validates a JWT. Returns the user_id string on success.

    Raises:
      TokenExpiredError  — token is valid but past expiry
      TokenInvalidError  — malformed, wrong type, or tampered
    """
    secret = _TOKEN_SECRETS[expected_type]
    try:
        payload = jwt.decode(token, secret, algorithms=[settings.ALGORITHM])
    except ExpiredSignatureError:
        raise TokenExpiredError("Token has expired. Please log in again.")
    except JWTError:
        raise TokenInvalidError("Token is invalid or has been tampered with.")

    # Token type check — prevents using a refresh token as an access token
    if payload.get("type") != expected_type.value:
        raise TokenInvalidError(f"Expected a {expected_type.value} token, got something else.")

    user_id = payload.get("sub")
    if not user_id:
        raise TokenInvalidError("Token is missing the 'sub' claim.")

    return user_id


def decode_access_token(token: str) -> str:
    """Returns user_id. Raises TokenExpiredError or TokenInvalidError."""
    return _decode_token(token, TokenType.ACCESS)


def decode_refresh_token(token: str) -> str:
    """Returns user_id. Raises TokenExpiredError or TokenInvalidError."""
    return _decode_token(token, TokenType.REFRESH)


# ── Password Strength Validation ──────────────────────────────────────────────
import re

_COMMON_PASSWORDS = {
    "password", "password1", "12345678", "123456789", "qwerty123",
    "iloveyou", "admin123", "letmein1", "welcome1", "monkey123",
}


def validate_password_strength(password: str) -> list[str]:
    """
    Returns a list of validation failure reasons (empty = password is strong).
    Applied at signup to enforce quality beyond just length.
    """
    errors: list[str] = []
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one number.")
    if password.lower() in _COMMON_PASSWORDS:
        errors.append("This password is too common. Please choose a unique one.")
    return errors
