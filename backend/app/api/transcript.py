import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.meeting import Meeting
from app.models.project import Project
from app.models.transcript import TranscriptSegment
from app.schemas.api import TranscriptUploadRequest, MeetingSummary, TranscriptSegmentOut
from app.schemas.transcript import NormalizedTranscript
from app.services.document_extraction_service import extract_transcript_text
from app.services.normalization import normalize_transcript

router = APIRouter(prefix="/transcripts", tags=["transcripts"])

# "official_transcript" is reserved for text/file uploads (highest
# reliability tier); audio uploads must pick one of these two.
_AUDIO_SOURCE_TYPES = {"meeting_bot_audio", "screen_share_audio"}


def _persist_meeting(
    db: Session, title: str, meeting_date: date | None, project_id: uuid.UUID | None,
    source_type: str, normalized: NormalizedTranscript,
) -> MeetingSummary:
    """
    Shared persistence path for every ingestion method (pasted text,
    uploaded file, uploaded audio, screen-capture audio) — the ONLY
    place a Meeting + TranscriptSegments get written, so everything
    downstream never needs to know how a meeting's transcript
    originally arrived.
    """
    meeting = Meeting(title=title, meeting_date=meeting_date, source_type=source_type, project_id=project_id)
    db.add(meeting)
    db.flush()

    for seg in normalized.segments:
        db.add(TranscriptSegment(
            meeting_id=meeting.id, segment_id=seg.segment_id, speaker=seg.speaker or "Unknown",
            timestamp=seg.timestamp_start, text=seg.text,
            source_line_start=seg.source_line_start or 0, source_line_end=seg.source_line_end or 0,
        ))

    db.commit()
    db.refresh(meeting)

    return MeetingSummary(
        id=meeting.id, title=meeting.title, meeting_date=meeting.meeting_date,
        source_type=meeting.source_type, project_id=meeting.project_id,
        segment_count=len(normalized.segments), created_at=meeting.created_at,
    )


def _validate_project(db: Session, project_id: uuid.UUID | None) -> None:
    if project_id is not None and not db.get(Project, project_id):
        raise HTTPException(status_code=404, detail="Project not found.")


@router.post("/upload", response_model=MeetingSummary)
def upload_transcript(payload: TranscriptUploadRequest, db: Session = Depends(get_db)):
    """Upload/paste raw transcript text directly (Stage 1)."""
    if not payload.raw_transcript.strip():
        raise HTTPException(status_code=400, detail="raw_transcript is empty.")

    _validate_project(db, payload.project_id)

    try:
        normalized = normalize_transcript(payload.raw_transcript)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not normalized.segments:
        raise HTTPException(status_code=400, detail="Could not extract any segments from the provided transcript.")

    return _persist_meeting(db, payload.title, payload.meeting_date, payload.project_id, "official_transcript", normalized)


@router.post("/upload-file", response_model=MeetingSummary)
async def upload_transcript_file(
    title: str = Form("Untitled Meeting"),
    meeting_date: date | None = Form(None),
    project_id: uuid.UUID | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a transcript as a file — .pdf, .docx, or .txt/.md."""
    _validate_project(db, project_id)

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        raw_text = extract_transcript_text(file.filename, file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        normalized = normalize_transcript(raw_text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not normalized.segments:
        raise HTTPException(status_code=400, detail="Could not extract any segments from this file's text.")

    return _persist_meeting(db, title, meeting_date, project_id, "official_transcript", normalized)


@router.post("/upload-audio", response_model=MeetingSummary)
async def upload_transcript_audio(
    title: str = Form("Untitled Meeting"),
    meeting_date: date | None = Form(None),
    project_id: uuid.UUID | None = Form(None),
    source_type: str = Form("meeting_bot_audio"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload an audio recording (Stage 5) — including screen/tab audio
    captured directly in the browser via getDisplayMedia, which the
    frontend uploads here with source_type="screen_share_audio".
    Runs Whisper transcription, then persists like any other source.
    """
    if source_type not in _AUDIO_SOURCE_TYPES:
        raise HTTPException(status_code=400, detail=f"source_type must be one of: {', '.join(sorted(_AUDIO_SOURCE_TYPES))}.")

    _validate_project(db, project_id)

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded audio file is empty.")

    # Imported lazily so environments that never use audio upload
    # don't pay faster-whisper's import cost on every app startup.
    from app.services.audio_transcription_service import transcribe_audio

    try:
        normalized = transcribe_audio(file_bytes, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _persist_meeting(db, title, meeting_date, project_id, source_type, normalized)


@router.get("/{meeting_id}/segments", response_model=list[TranscriptSegmentOut])
def get_segments(meeting_id: uuid.UUID, db: Session = Depends(get_db)):
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found.")

    return (
        db.query(TranscriptSegment)
        .filter(TranscriptSegment.meeting_id == meeting_id)
        .order_by(TranscriptSegment.source_line_start)
        .all()
    )


@router.get("", response_model=list[MeetingSummary])
def list_meetings(db: Session = Depends(get_db)):
    meetings = db.query(Meeting).order_by(Meeting.created_at.desc()).all()
    out = []
    for m in meetings:
        count = db.query(TranscriptSegment).filter(TranscriptSegment.meeting_id == m.id).count()
        out.append(MeetingSummary(
            id=m.id, title=m.title, meeting_date=m.meeting_date, source_type=m.source_type,
            project_id=m.project_id, segment_count=count, created_at=m.created_at,
        ))
    return out