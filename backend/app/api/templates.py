import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.document_template import DocumentTemplate
from app.schemas.template_api import DocumentTemplateOut, DocumentTemplateSummary
from app.services.template_upload_service import upload_and_classify_template

router = APIRouter(prefix="/templates", tags=["templates"])


@router.post("/upload", response_model=DocumentTemplateOut)
async def upload_template(
    name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Stage 4 entry point: upload a client's own document template
    (.docx). Parses its structure and classifies every section.
    """
    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx templates are supported.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        template = upload_and_classify_template(db, file_bytes=file_bytes, name=name, original_filename=file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return template


@router.get("", response_model=list[DocumentTemplateSummary])
def list_templates(db: Session = Depends(get_db)):
    templates = db.query(DocumentTemplate).order_by(DocumentTemplate.created_at.desc()).all()
    return [
        DocumentTemplateSummary(
            id=t.id, name=t.name, original_filename=t.original_filename,
            section_count=len(t.sections), created_at=t.created_at,
        )
        for t in templates
    ]


@router.get("/{template_id}", response_model=DocumentTemplateOut)
def get_template(template_id: uuid.UUID, db: Session = Depends(get_db)):
    template = db.get(DocumentTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found.")
    return template