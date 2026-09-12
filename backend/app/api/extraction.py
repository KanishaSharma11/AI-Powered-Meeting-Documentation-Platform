import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.extraction import ExtractedItem
from app.models.meeting import Meeting
from app.schemas.api import ExtractedItemOut, ExtractionRunResult, ReviewAction
from app.services.extraction_service import run_extraction
from app.services.fusion_service import maybe_fuse_item

router = APIRouter(tags=["extraction"])


def _to_out(item: ExtractedItem) -> ExtractedItemOut:
    return ExtractedItemOut(
        id=item.id,
        item_type=item.item_type,
        agent_name=item.agent_name,
        text=item.text,
        owner=item.owner,
        due_date=item.due_date,
        segment_id=item.segment_id,
        evidence_speaker=item.evidence_speaker,
        evidence_timestamp=item.evidence_timestamp,
        evidence_text=item.evidence_text,
        extraction_confidence=item.extraction_confidence,
        source_baseline_confidence=item.source_baseline_confidence,
        combined_confidence=item.combined_confidence,
        low_confidence=item.combined_confidence < settings.LOW_CONFIDENCE_THRESHOLD,
        review_status=item.review_status,
        edited_text=item.edited_text,
        final_text=item.final_text,
        project_fact_id=item.project_fact_id,
    )


@router.post("/meetings/{meeting_id}/extract", response_model=ExtractionRunResult)
def extract_meeting(meeting_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Runs all three extraction agents (Section 2.5) over the meeting's
    transcript and persists evidence-linked, confidence-scored items
    ready for human review (Section 2.7). Safe to re-run — a prior
    run's items are replaced.
    """
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found.")

    try:
        items = run_extraction(db, meeting)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    def count(t):
        return len([i for i in items if i.item_type == t])

    return ExtractionRunResult(
        meeting_id=meeting.id,
        requirements_count=count("requirement"),
        decisions_count=count("decision"),
        action_items_count=count("action_item"),
        risks_count=len(
            [i for i in items if i.item_type in ("risk", "blocker", "open_question")]
        ),
        items=[_to_out(i) for i in items],
    )


@router.get("/meetings/{meeting_id}/extractions", response_model=list[ExtractedItemOut])
def list_extractions(meeting_id: uuid.UUID, db: Session = Depends(get_db)):
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found.")

    items = (
        db.query(ExtractedItem)
        .filter(ExtractedItem.meeting_id == meeting_id)
        .order_by(ExtractedItem.item_type, ExtractedItem.created_at)
        .all()
    )
    return [_to_out(i) for i in items]


@router.patch("/extractions/{item_id}", response_model=ExtractedItemOut)
def review_item(item_id: uuid.UUID, payload: ReviewAction, db: Session = Depends(get_db)):
    """
    Human Review & Approval (Section 2.2 step 7). Accept, edit, or
    reject a single extracted item. Only accepted/edited items are
    included when a MOM is later generated.
    """
    item = db.get(ExtractedItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Extracted item not found.")

    action = payload.action.lower().strip()
    if action not in ("accept", "edit", "reject"):
        raise HTTPException(
            status_code=400, detail="action must be one of: accept, edit, reject."
        )

    if action == "accept":
        item.review_status = "accepted"
        item.edited_text = None
    elif action == "reject":
        item.review_status = "rejected"
        item.edited_text = None
    elif action == "edit":
        if not payload.edited_text or not payload.edited_text.strip():
            raise HTTPException(
                status_code=400, detail="edited_text is required when action='edit'."
            )
        item.review_status = "edited"
        item.edited_text = payload.edited_text.strip()

    item.reviewed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(item)

    # Stage 3: reconcile into project-level knowledge, if this
    # meeting belongs to a project. No-ops otherwise (see
    # services/fusion_service.py).
    if action in ("accept", "edit"):
        maybe_fuse_item(db, item)
        db.refresh(item)

    return _to_out(item)