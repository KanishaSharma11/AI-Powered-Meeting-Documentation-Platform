from pydantic import BaseModel, Field

class TranscriptSegment(BaseModel):
    segment_id: str
    speaker: str | None = None
    timestamp_start: str | None = None
    timestamp_end: str | None = None
    text: str
    source_line_start: int | None = None
    source_line_end: int | None = None

class NormalizedTranscript(BaseModel):
    segments: list[TranscriptSegment] = Field(default_factory=list)
    original_text: str
    source_format: str

    