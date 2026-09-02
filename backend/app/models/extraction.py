import uuid
from datetime import datetime

from backend.app.models.meeting import Meeting
from sqlalchemy import String, Text, Float, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ExtractedItem(Base):
    """
    A single AI-extracted, evidence-linked fact: a requirement,
    decision, action item, or risk/open question.

    One table is used for all four item types (rather than four
    separate tables) because they share the same evidence + confidence
    + human-review lifecycle described in Sections 1.3 and 2.5-2.7 of
    the project plan. `item_type` and the optional owner/due_date
    fields differentiate them.
    """

    __tablename__ = "extracted_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("meetings.id"), nullable=False
    )

    # requirement | decision | action_item | risk | open_question
    item_type: Mapped[str] = mapped_column(String(30), nullable=False)

    # Which agent produced this (Section 2.5) — kept for traceability.
    agent_name: Mapped[str] = mapped_column(String(60), nullable=False)

    text: Mapped[str] = mapped_column(Text, nullable=False)

    # Only populated for action_item.
    owner: Mapped[str | None] = mapped_column(String(120), nullable=True)
    due_date: Mapped[str | None] = mapped_column(String(60), nullable=True)

    # --- Evidence (Section 1.3) ---
    segment_id: Mapped[str] = mapped_column(
        ForeignKey("transcript_segments.segment_id"), nullable=True
    )
    evidence_speaker: Mapped[str | None] = mapped_column(String(120), nullable=True)
    evidence_timestamp: Mapped[str | None] = mapped_column(String(20), nullable=True)
    evidence_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Confidence (Section 2.3 + 2.4) ---
    extraction_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    source_baseline_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    combined_confidence: Mapped[float] = mapped_column(Float, default=0.0)

    # --- Human review (Section 2.2 step 7 / 2.7) ---
    # pending | accepted | edited | rejected
    review_status: Mapped[str] = mapped_column(String(20), default="pending")
    edited_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    meeting: Mapped["Meeting"] = relationship("Meeting", back_populates="extracted_items")

    @property
    def final_text(self) -> str:
        """Text that should appear in the generated document."""
        if self.review_status == "edited" and self.edited_text:
            return self.edited_text
        return self.text