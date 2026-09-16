import uuid
from datetime import datetime

from sqlalchemy import String, Text, Float, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ProjectFact(Base):
    """
    The canonical, deduplicated, project-level version of one
    requirement/decision/action item/risk (Section 2.4).

    status: "active" (canonical_text is current) or "conflicted"
    (a later meeting contradicted it — flagged for human resolution,
    never silently overwritten).
    """

    __tablename__ = "project_facts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    fact_type: Mapped[str] = mapped_column(String(30), nullable=False)
    canonical_text: Mapped[str] = mapped_column(Text, nullable=False)
    owner: Mapped[str | None] = mapped_column(String(120), nullable=True)
    due_date: Mapped[str | None] = mapped_column(String(60), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    first_meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("meetings.id"), nullable=False
    )
    last_meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("meetings.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project: Mapped["Project"] = relationship("Project", back_populates="facts")
    revisions: Mapped[list["ProjectFactRevision"]] = relationship(
        "ProjectFactRevision",
        back_populates="fact",
        cascade="all, delete-orphan",
        order_by="ProjectFactRevision.created_at",
    )


class ProjectFactRevision(Base):
    """
    One meeting's mention of a ProjectFact — the timeline entry.
    relation: "initial" | "duplicate" | "conflict" | "resolution"
    """

    __tablename__ = "project_fact_revisions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    fact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project_facts.id"), nullable=False
    )
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("meetings.id"), nullable=False
    )
    extracted_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("extracted_items.id"), nullable=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    relation: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    fact: Mapped["ProjectFact"] = relationship("ProjectFact", back_populates="revisions")