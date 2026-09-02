import uuid

from backend.app.models.meeting import Meeting
from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TranscriptSegment(Base):
    """
    One normalized segment of a meeting transcript.

    This is the authoritative, application-owned record of "what was
    said". AI agents never see or write to this table directly — they
    only ever reference a segment_id. Evidence resolution (Section 1.3)
    reads speaker/timestamp/text back out of this table.
    """

    __tablename__ = "transcript_segments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("meetings.id"), nullable=False
    )

    # Human-readable, stable ID like "SEG-0001". This is what the LLM
    # is instructed to cite as evidence — never the internal UUID.
    segment_id: Mapped[str] = mapped_column(String(20), nullable=False)

    speaker: Mapped[str] = mapped_column(String(120), default="Unknown")
    timestamp: Mapped[str | None] = mapped_column(String(20), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    source_line_start: Mapped[int] = mapped_column(Integer, default=0)
    source_line_end: Mapped[int] = mapped_column(Integer, default=0)

    meeting: Mapped["Meeting"] = relationship("Meeting", back_populates="segments")