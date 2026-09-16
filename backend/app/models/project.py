import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Project(Base):
    """
    Groups multiple meetings together so facts can be reconciled
    across them (Stage 3 — Knowledge Fusion, Section 2.4).
    """

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    meetings: Mapped[list["Meeting"]] = relationship(
        "Meeting", back_populates="project"
    )
    facts: Mapped[list["ProjectFact"]] = relationship(
        "ProjectFact", back_populates="project", cascade="all, delete-orphan"
    )