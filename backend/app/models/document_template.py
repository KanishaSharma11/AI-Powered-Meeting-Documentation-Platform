import uuid
from datetime import datetime

from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.project import Project
from app.models.meeting import Meeting


class DocumentTemplate(Base):
    """A client-uploaded document template (Section 2.6, Stage 4)."""

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

    content_type: requirement | decision | action_item |
    risk_or_question | participants | custom_text | dynamic_custom
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
    table_columns: Mapped[list | None] = mapped_column(JSON, nullable=True)
    static_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    custom_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    template: Mapped["DocumentTemplate"] = relationship(
        "DocumentTemplate", back_populates="sections"
    )