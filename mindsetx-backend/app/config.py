"""
config.py — Application settings loaded from environment / .env file.

All secrets are required — the app will refuse to start if any are missing.
Use pydantic-settings for automatic .env loading + type coercion.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── App ───────────────────────────────────────────────────────────────────
    APP_ENV: str = "development"

    # ── JWT ───────────────────────────────────────────────────────────────────
    # Two separate secrets — allows rotating refresh tokens independently
    SECRET_KEY: str                   # Used for access tokens
    REFRESH_SECRET_KEY: str           # Used for refresh tokens — must differ from SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60      # 1 hour
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7         # 7 days

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str                  # postgresql+asyncpg://...

    # ── AI ────────────────────────────────────────────────────────────────────
    OPENAI_API_KEY: str

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 30
    AUTH_RATE_LIMIT: str = "5/minute"  # Stricter limit for login/signup

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
