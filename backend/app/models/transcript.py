import uuid

from sqlalchemy import String, Text, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.meeting import Meeting


class TranscriptSegment(Base):
    """
    One normalized segment of a meeting transcript.

    This is the authoritative, application-owned record of "what was
    said". AI agents never see or write to this table directly — they
    only ever reference a segment_id. Evidence resolution (Section 1.3)
    reads speaker/timestamp/text back out of this table.
    """

    __tablename__ = "transcript_segments"
    __table_args__ = (
        # segment_id (e.g. "SEG-0001") resets per meeting, so it is
        # only unique in combination with meeting_id — never on its
        # own. This composite constraint is what extracted_items'
        # composite foreign key (see models/extraction.py) points at.
        UniqueConstraint(
            "meeting_id", "segment_id", name="uq_transcript_segments_meeting_segment"
        ),
    )

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