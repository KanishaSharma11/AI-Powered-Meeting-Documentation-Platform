import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------- Transcript upload ----------

class TranscriptUploadRequest(BaseModel):
    title: str = Field(default="Untitled Meeting")
    meeting_date: date | None = None
    raw_transcript: str = Field(description="Raw transcript text, pasted or uploaded.")


class MeetingSummary(BaseModel):
    id: uuid.UUID
    title: str
    meeting_date: date | None
    source_type: str
    segment_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TranscriptSegmentOut(BaseModel):
    segment_id: str
    speaker: str
    timestamp: str | None
    text: str

    model_config = ConfigDict(from_attributes=True)


# ---------- Extraction / review ----------

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
    edited_text: str | None = Field(
        default=None, description="Required when action='edit'."
    )