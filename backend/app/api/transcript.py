import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.meeting import Meeting
from app.models.project import Project
from app.models.transcript import TranscriptSegment
from app.schemas.api import TranscriptUploadRequest, MeetingSummary, TranscriptSegmentOut
from app.services.normalization import normalize_transcript

router = APIRouter(prefix="/transcripts", tags=["transcripts"])


@router.post("/upload", response_model=MeetingSummary)
def upload_transcript(payload: TranscriptUploadRequest, db: Session = Depends(get_db)):
    """
    Stage 1 entry point: upload/paste a raw transcript, get back a
    Meeting with normalized segments ready for extraction. Optionally
    pass project_id (Stage 3) to have accepted/edited items from this
    meeting reconciled against that project's existing knowledge.
    """
    if not payload.raw_transcript.strip():
        raise HTTPException(status_code=400, detail="raw_transcript is empty.")

    if payload.project_id is not None:
        project = db.get(Project, payload.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found.")

    try:
        normalized = normalize_transcript(payload.raw_transcript)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not normalized.segments:
        raise HTTPException(
            status_code=400,
            detail="Could not extract any segments from the provided transcript.",
        )

    meeting = Meeting(
        title=payload.title,
        meeting_date=payload.meeting_date,
        source_type="official_transcript",
        project_id=payload.project_id,
    )
    db.add(meeting)
    db.flush()  # get meeting.id before inserting segments

    for seg in normalized.segments:
        db.add(
            TranscriptSegment(
                meeting_id=meeting.id,
                segment_id=seg.segment_id,
                speaker=seg.speaker or "Unknown",
                timestamp=seg.timestamp_start,
                text=seg.text,
                source_line_start=seg.source_line_start or 0,
                source_line_end=seg.source_line_end or 0,
            )
        )

    db.commit()
    db.refresh(meeting)

    return MeetingSummary(
        id=meeting.id,
        title=meeting.title,
        meeting_date=meeting.meeting_date,
        source_type=meeting.source_type,
        project_id=meeting.project_id,
        segment_count=len(normalized.segments),
        created_at=meeting.created_at,
    )


@router.get("/{meeting_id}/segments", response_model=list[TranscriptSegmentOut])
def get_segments(meeting_id: uuid.UUID, db: Session = Depends(get_db)):
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found.")

    segments = (
        db.query(TranscriptSegment)
        .filter(TranscriptSegment.meeting_id == meeting_id)
        .order_by(TranscriptSegment.source_line_start)
        .all()
    )
    return segments


@router.get("", response_model=list[MeetingSummary])
def list_meetings(db: Session = Depends(get_db)):
    meetings = db.query(Meeting).order_by(Meeting.created_at.desc()).all()
    out = []
    for m in meetings:
        count = (
            db.query(TranscriptSegment)
            .filter(TranscriptSegment.meeting_id == m.id)
            .count()
        )
        out.append(
            MeetingSummary(
                id=m.id,
                title=m.title,
                meeting_date=m.meeting_date,
                source_type=m.source_type,
                project_id=m.project_id,
                segment_count=count,
                created_at=m.created_at,
            )
        )
    return out