import uuid
from datetime import datetime, date

from sqlalchemy import String, Date, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Meeting(Base):
    """
    A single meeting/session. Everything else (transcript segments,
    extracted items, generated MOM) hangs off this record.
    """

    __tablename__ = "meetings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    title: Mapped[str] = mapped_column(String(255), default="Untitled Meeting")

    meeting_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Where this meeting's transcript came from. Stage 1/2 always use
    # "official_transcript"; later stages add bot/screen-share sources.
    source_type: Mapped[str] = mapped_column(String(50), default="official_transcript")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    segments: Mapped[list["TranscriptSegment"]] = relationship(
        "TranscriptSegment", back_populates="meeting", cascade="all, delete-orphan"
    )

    extracted_items: Mapped[list["ExtractedItem"]] = relationship(
        "ExtractedItem", back_populates="meeting", cascade="all, delete-orphan"
    )