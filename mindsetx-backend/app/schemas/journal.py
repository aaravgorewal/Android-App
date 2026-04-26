import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class JournalCreate(BaseModel):
    content: str = Field(
        min_length=10,
        max_length=5000,
        description="The raw thought/journal entry from the user.",
    )


class JournalResponse(BaseModel):
    id: uuid.UUID
    content: str
    distortion_pattern: str | None
    reframed_thought: str | None
    suggested_action: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReframeRequest(BaseModel):
    content: str = Field(
        min_length=10,
        max_length=5000,
        description="The thought text to reframe via AI.",
    )


class ReframeResponse(BaseModel):
    pattern: str
    reframe: str
    action: str
