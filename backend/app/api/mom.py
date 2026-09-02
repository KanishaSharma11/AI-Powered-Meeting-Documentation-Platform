import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import io

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.extraction import ExtractedItem
from app.models.meeting import Meeting
from app.models.transcript import TranscriptSegment
from app.schemas.mom import MOMDocument
from app.services.mom_service import build_mom_document_model, render_mom_docx

router = APIRouter(prefix="/meetings", tags=["mom"])


@router.get("/{meeting_id}/mom/preview", response_model=MOMDocument)
def preview_mom(meeting_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Returns the MOM content as JSON (built only from accepted/edited
    review items) so the review UI can show a live preview before
    the reviewer downloads the .docx.
    """
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found.")

    items = (
        db.query(ExtractedItem).filter(ExtractedItem.meeting_id == meeting_id).all()
    )
    segments = (
        db.query(TranscriptSegment)
        .filter(TranscriptSegment.meeting_id == meeting_id)
        .all()
    )

    return build_mom_document_model(meeting, items, segments)


@router.get("/{meeting_id}/mom/download")
def download_mom(meeting_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Generates the .docx MOM from accepted/edited items and streams it
    back (Section 2.2 step 6-7: "Download button provides the
    finished file (Word/PDF) once the reviewer is satisfied").
    """
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found.")

    items = (
        db.query(ExtractedItem).filter(ExtractedItem.meeting_id == meeting_id).all()
    )
    if not items:
        raise HTTPException(
            status_code=400,
            detail="No extracted items found. Run extraction first.",
        )

    approved = [i for i in items if i.review_status in ("accepted", "edited")]
    if not approved:
        raise HTTPException(
            status_code=400,
            detail="No items have been accepted or edited yet. "
            "Review extracted items before generating the MOM.",
        )

    segments = (
        db.query(TranscriptSegment)
        .filter(TranscriptSegment.meeting_id == meeting_id)
        .all()
    )

    mom_model = build_mom_document_model(meeting, items, segments)
    docx_bytes = render_mom_docx(mom_model)

    filename = f"MOM_{meeting.title.replace(' ', '_')}.docx"

    return StreamingResponse(
        io.BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )