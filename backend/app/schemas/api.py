import uuid
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field


class ProjectCreateRequest(BaseModel):
    name: str
    description: str | None = None


class ProjectOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    meeting_count: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TranscriptUploadRequest(BaseModel):
    title: str = Field(default="Untitled Meeting")
    meeting_date: date | None = None
    raw_transcript: str = Field(description="Raw transcript text, pasted or uploaded.")
    project_id: uuid.UUID | None = Field(
        default=None,
        description=(
            "Optional. When set, accepted/edited items from this "
            "meeting are reconciled against the project's existing "
            "facts (Stage 3 knowledge fusion)."
        ),
    )


class MeetingSummary(BaseModel):
    id: uuid.UUID
    title: str
    meeting_date: date | None
    source_type: str
    project_id: uuid.UUID | None
    segment_count: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TranscriptSegmentOut(BaseModel):
    segment_id: str
    speaker: str
    timestamp: str | None
    text: str
    model_config = ConfigDict(from_attributes=True)


class ExtractedItemOut(BaseModel):
    id: uuid.UUID
    item_type: str
    agent_name: str
    text: str
    owner: str | None
    due_date: str | None
    segment_id: str | None
    evidence_speaker: str | None
    evidence_timestamp: str | None
    evidence_text: str | None
    extraction_confidence: float
    source_baseline_confidence: float
    combined_confidence: float
    low_confidence: bool
    review_status: str
    edited_text: str | None
    final_text: str
    project_fact_id: uuid.UUID | None
    model_config = ConfigDict(from_attributes=True)


class ExtractionRunResult(BaseModel):
    meeting_id: uuid.UUID
    requirements_count: int
    decisions_count: int
    action_items_count: int
    risks_count: int
    items: list[ExtractedItemOut]


class ReviewAction(BaseModel):
    action: str = Field(description="One of: accept, edit, reject")
    edited_text: str | None = Field(default=None, description="Required when action='edit'.")


class ProjectFactRevisionOut(BaseModel):
    id: uuid.UUID
    meeting_id: uuid.UUID
    text: str
    relation: str
    confidence: float
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ProjectFactOut(BaseModel):
    id: uuid.UUID
    fact_type: str
    canonical_text: str
    owner: str | None
    due_date: str | None
    status: str
    confidence: float
    first_meeting_id: uuid.UUID
    last_meeting_id: uuid.UUID
    revisions: list[ProjectFactRevisionOut]
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ResolveConflictRequest(BaseModel):
    chosen_revision_id: uuid.UUID | None = Field(
        default=None, description="Adopt the text of this existing revision as canonical."
    )
    custom_text: str | None = Field(
        default=None, description="Or: write new canonical text directly."
    )