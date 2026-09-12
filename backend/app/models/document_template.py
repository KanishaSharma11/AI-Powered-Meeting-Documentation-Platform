import uuid
from datetime import datetime

from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DocumentTemplate(Base):
    """
    A client-uploaded document template (Section 2.6: "Doc Intelligence
    Layer" / Stage 4). Parsed once at upload time into an ordered list
    of TemplateSections — that parse is the "Template Schema" the plan
    refers to. Generation (services/document_generator_service.py)
    replays this structure with real content substituted in.
    """

    __tablename__ = "document_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    sections: Mapped[list["TemplateSection"]] = relationship(
        "TemplateSection",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="TemplateSection.order_index",
    )


class TemplateSection(Base):
    """
    One section of a parsed template, in original document order.

    content_type uses the SAME vocabulary as Stage 3's fusion groups
    (requirement | decision | action_item | risk_or_question) plus
    three generation-only types:
      - "participants"     populated from meeting/project speakers
      - "custom_text"      not data-driven — static_text is reproduced
                            verbatim (e.g. a "Purpose" or "Scope"
                            section that's boilerplate, not extracted
                            content)
      - "dynamic_custom"    expects meeting-specific content but
                            doesn't match any fixed type (e.g. "Budget
                            Notes") — populated by live, evidence-
                            grounded extraction at generation time
                            using custom_description as the criteria

    The shared fixed-type vocabulary is what lets Stage 4 generation
    pull directly from Stage 3's ProjectFact table (or Stage 1/2's
    ExtractedItem, for a standalone meeting) with no translation layer.
    """

    __tablename__ = "template_sections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_templates.id"), nullable=False
    )

    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    heading_text: Mapped[str] = mapped_column(String(255), nullable=False)
    heading_level: Mapped[int] = mapped_column(Integer, default=1)

    content_type: Mapped[str] = mapped_column(String(30), nullable=False)

    is_table: Mapped[bool] = mapped_column(Boolean, default=False)
    # List[str] of header row column names, only set when is_table.
    table_columns: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Raw paragraph text captured under this heading in the original
    # template — only used when content_type == "custom_text".
    static_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Only set when content_type == "dynamic_custom": a natural-
    # language description (written by TemplateSchemaAgent) of what
    # kind of meeting content belongs here. Guides live extraction at
    # generation time (see ai/agents/dynamic_section_agent.py).
    custom_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    template: Mapped["DocumentTemplate"] = relationship(
        "DocumentTemplate", back_populates="sections"
    )