import io
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.document_template import DocumentTemplate
from app.models.meeting import Meeting
from app.services.document_generator_service import generate_document

router = APIRouter(prefix="/meetings", tags=["documents"])


@router.get("/{meeting_id}/documents/{template_id}/download")
def download_document(
    meeting_id: uuid.UUID, template_id: uuid.UUID, db: Session = Depends(get_db)
):
    """
    Dynamic Document Generator (Section 2.6 step 4 / 2.7): renders a
    .docx for this meeting that mirrors the given template's own
    structure, populated with real content instead of placeholder
    text.
    """
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found.")

    template = db.get(DocumentTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found.")

    docx_bytes = generate_document(db, meeting, template)

    filename = f"{template.name.replace(' ', '_')}_{meeting.title.replace(' ', '_')}.docx"

    return StreamingResponse(
        io.BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )