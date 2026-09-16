import uuid
from sqlalchemy.orm import Session
from app.ai.agents.requirements_decisions_agent import RequirementsDecisionsAgent
from app.ai.agents.action_items_agent import ActionItemsAgent
from app.ai.agents.risks_agent import RisksAgent
from app.core.config import settings
from app.models.extraction import ExtractedItem
from app.models.meeting import Meeting
from app.models.transcript import TranscriptSegment
from app.services.normalization import render_segments_for_prompt

def _resolve_evidence(db, meeting_id, segment_id):
    if not segment_id: return None
    return db.query(TranscriptSegment).filter(TranscriptSegment.meeting_id == meeting_id, TranscriptSegment.segment_id == segment_id).first()

def _combined_confidence(baseline, extraction_confidence):
    return round(baseline * extraction_confidence, 4)

def run_extraction(db: Session, meeting: Meeting):
    segments = db.query(TranscriptSegment).filter(TranscriptSegment.meeting_id == meeting.id).order_by(TranscriptSegment.source_line_start).all()
    if not segments:
        raise ValueError("Meeting has no transcript segments to extract from.")
    transcript_block = render_segments_for_prompt(segments)
    baseline = settings.SOURCE_BASELINE_CONFIDENCE.get(meeting.source_type, settings.SOURCE_BASELINE_CONFIDENCE["official_transcript"])
    db.query(ExtractedItem).filter(ExtractedItem.meeting_id == meeting.id).delete()
    created = []
    req_dec_result = RequirementsDecisionsAgent().extract(transcript_block)
    for req in req_dec_result.requirements:
        created.append(_build_item(db, meeting.id, "requirement", "requirements_decisions_agent", req.text, req.evidence.segment_id, req.confidence, baseline))
    for dec in req_dec_result.decisions:
        created.append(_build_item(db, meeting.id, "decision", "requirements_decisions_agent", dec.text, dec.evidence.segment_id, dec.confidence, baseline))
    action_result = ActionItemsAgent().extract(transcript_block)
    for item in action_result.action_items:
        created.append(_build_item(db, meeting.id, "action_item", "action_items_agent", item.text, item.evidence.segment_id, item.confidence, baseline, owner=item.owner, due_date=item.due_date))
    risks_result = RisksAgent().extract(transcript_block)
    for item in risks_result.items:
        created.append(_build_item(db, meeting.id, item.category, "risks_agent", item.text, item.evidence.segment_id, item.confidence, baseline))
    db.add_all(created)
    db.commit()
    for item in created:
        db.refresh(item)
    return created

def _build_item(db, meeting_id, item_type, agent_name, text, segment_id, extraction_confidence, baseline, owner=None, due_date=None):
    evidence = _resolve_evidence(db, meeting_id, segment_id)
    return ExtractedItem(
        meeting_id=meeting_id, item_type=item_type, agent_name=agent_name, text=text, owner=owner, due_date=due_date,
        segment_id=evidence.segment_id if evidence else None,
        evidence_speaker=evidence.speaker if evidence else None,
        evidence_timestamp=evidence.timestamp if evidence else None,
        evidence_text=evidence.text if evidence else None,
        extraction_confidence=extraction_confidence, source_baseline_confidence=baseline,
        combined_confidence=_combined_confidence(baseline, extraction_confidence), review_status="pending",
    )