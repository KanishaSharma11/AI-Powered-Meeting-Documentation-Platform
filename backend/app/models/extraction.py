import uuid
from datetime import datetime

from sqlalchemy import String, Text, Float, DateTime, ForeignKey, ForeignKeyConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.meeting import Meeting

class ExtractedItem(Base):
    """
    A single AI-extracted, evidence-linked fact: a requirement,
    decision, action item, or risk/open question.
    """

    __tablename__ = "extracted_items"
    __table_args__ = (
        # Composite FK, not single-column on segment_id: segment IDs
        # like "SEG-0001" reset per meeting, so only (meeting_id,
        # segment_id) together identifies one real segment.
        ForeignKeyConstraint(
            ["meeting_id", "segment_id"],
            ["transcript_segments.meeting_id", "transcript_segments.segment_id"],
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("meetings.id"), nullable=False
    )

    # requirement | decision | action_item | risk | blocker | open_question
    item_type: Mapped[str] = mapped_column(String(30), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(60), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    owner: Mapped[str | None] = mapped_column(String(120), nullable=True)
    due_date: Mapped[str | None] = mapped_column(String(60), nullable=True)

    segment_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    evidence_speaker: Mapped[str | None] = mapped_column(String(120), nullable=True)
    evidence_timestamp: Mapped[str | None] = mapped_column(String(20), nullable=True)
    evidence_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    extraction_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    source_baseline_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    combined_confidence: Mapped[float] = mapped_column(Float, default=0.0)

    # pending | accepted | edited | rejected
    review_status: Mapped[str] = mapped_column(String(20), default="pending")
    edited_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Stage 3: set once this item has been reconciled into a
    # project-level fact.
    project_fact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project_facts.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    meeting: Mapped["Meeting"] = relationship("Meeting", back_populates="extracted_items")

    @property
    def final_text(self) -> str:
        if self.review_status == "edited" and self.edited_text:
            return self.edited_text
        return self.text