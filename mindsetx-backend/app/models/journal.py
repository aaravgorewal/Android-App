import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Raw thought text (sensitive — never log this)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # AI Reframe output (stored after processing)
    distortion_pattern: Mapped[str] = mapped_column(String(120), nullable=True)
    reframed_thought: Mapped[str] = mapped_column(Text, nullable=True)
    suggested_action: Mapped[str] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    user = relationship("User", back_populates="journal_entries", lazy="selectin")

    def __repr__(self) -> str:
        return f"<JournalEntry id={self.id} user_id={self.user_id}>"
