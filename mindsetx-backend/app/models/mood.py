import uuid
from datetime import date, datetime
from sqlalchemy import Integer, Date, DateTime, ForeignKey, func, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class MoodLog(Base):
    __tablename__ = "mood_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # 1 = Down, 2 = Okay, 3 = Good, 4 = Great
    mood_score: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    log_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("mood_score >= 1 AND mood_score <= 4", name="mood_score_range"),
    )

    user = relationship("User", back_populates="mood_logs", lazy="selectin")

    def __repr__(self) -> str:
        return f"<MoodLog id={self.id} user_id={self.user_id} score={self.mood_score}>"
