import io
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_role
from app.models.document_template import DocumentTemplate
from app.models.generated_document import GeneratedDocument
from app.models.meeting import Meeting
from app.models.user import User
from app.schemas.document_api import GeneratedDocumentSummary
from app.services.audit_service import log_action
from app.services.document_generator_service import generate_document

# Meeting-scoped: generate a new version, list history.
meeting_documents_router = APIRouter(prefix="/meetings", tags=["documents"])
# Not meeting-scoped: a generated document's own id is globally unique.
documents_router = APIRouter(prefix="/documents", tags=["documents"])


@meeting_documents_router.post("/{meeting_id}/documents/generate", response_model=GeneratedDocumentSummary)
def generate_and_save_document(
    meeting_id: uuid.UUID,
    template_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("reviewer", "admin")),
):
    """
    Dynamic Document Generator with versioning: every call creates a
    new persisted version rather than only streaming bytes back.
    """
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found.")

    template = db.get(DocumentTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found.")

    docx_bytes = generate_document(db, meeting, template)
    filename = f"{template.name.replace(' ', '_')}_{meeting.title.replace(' ', '_')}.docx"

    last_version = (
        db.query(GeneratedDocument)
        .filter(GeneratedDocument.meeting_id == meeting_id, GeneratedDocument.template_id == template_id)
        .order_by(GeneratedDocument.version.desc())
        .first()
    )
    next_version = (last_version.version + 1) if last_version else 1

    record = GeneratedDocument(
        meeting_id=meeting_id, template_id=template_id, version=next_version,
        filename=filename, file_bytes=docx_bytes,
        generated_by_user_id=user.id, generated_by_email=user.email,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    log_action(
        db, user, "generate_document", "generated_document", str(record.id),
        meta={"meeting_id": str(meeting_id), "template_id": str(template_id), "version": next_version},
    )

    return record


@meeting_documents_router.get("/{meeting_id}/documents", response_model=list[GeneratedDocumentSummary])
def list_generated_documents(meeting_id: uuid.UUID, db: Session = Depends(get_db)):
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found.")

    return (
        db.query(GeneratedDocument)
        .filter(GeneratedDocument.meeting_id == meeting_id)
        .order_by(GeneratedDocument.version.desc())
        .all()
    )


@documents_router.get("/{document_id}/download")
def download_generated_document(document_id: uuid.UUID, db: Session = Depends(get_db)):
    record = db.get(GeneratedDocument, document_id)
    if not record:
        raise HTTPException(status_code=404, detail="Generated document not found.")

    return StreamingResponse(
        io.BytesIO(record.file_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{record.filename}"'},
    )