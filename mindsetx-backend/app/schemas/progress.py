import uuid
from datetime import date
from typing import List
from pydantic import BaseModel, Field


class MoodCreate(BaseModel):
    mood_score: int = Field(ge=1, le=4, description="1=Down, 2=Okay, 3=Good, 4=Great")
    log_date: date | None = None  # Defaults to today if not provided


class MoodEntry(BaseModel):
    date: date
    mood_score: int

    model_config = {"from_attributes": True}


class ProgressResponse(BaseModel):
    current_streak: int
    longest_streak: int
    weekly_moods: List[MoodEntry]
    total_entries: int
    insight: str | None = None
