"""
AI Information Extraction orchestration (Section 2.5) +
Confidence & Conflict Analysis (Section 2.2 step 5, simplified).

Runs the three specialized agents over a meeting's transcript,
resolves each returned segment_id against the authoritative
TranscriptSegment table (Section 1.3 — evidence comes from the app,
never the LLM), computes a combined confidence score, and persists
everything as ExtractedItem rows for the review UI to work with.
"""

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


def _resolve_evidence(
    db: Session, meeting_id: uuid.UUID, segment_id: str | None
) -> TranscriptSegment | None:
    if not segment_id:
        return None
    return (
        db.query(TranscriptSegment)
        .filter(
            TranscriptSegment.meeting_id == meeting_id,
            TranscriptSegment.segment_id == segment_id,
        )
        .first()
    )


def _combined_confidence(baseline: float, extraction_confidence: float) -> float:
    # Simple, explainable combination (Section 2.4: "each fused fact
    # carries forward the confidence of its best-supporting source").
    # A statement can never be more trustworthy than the transcription
    # of the source it came from.
    return round(baseline * extraction_confidence, 4)


def run_extraction(db: Session, meeting: Meeting) -> list[ExtractedItem]:
    segments = (
        db.query(TranscriptSegment)
        .filter(TranscriptSegment.meeting_id == meeting.id)
        .order_by(TranscriptSegment.source_line_start)
        .all()
    )

    if not segments:
        raise ValueError("Meeting has no transcript segments to extract from.")

    transcript_block = render_segments_for_prompt(
        [
            type(
                "S",
                (),
                {
                    "segment_id": s.segment_id,
                    "speaker": s.speaker,
                    "timestamp_start": s.timestamp,
                    "text": s.text,
                },
            )()
            for s in segments
        ]
    )

    baseline = settings.SOURCE_BASELINE_CONFIDENCE.get(
        meeting.source_type, settings.SOURCE_BASELINE_CONFIDENCE["official_transcript"]
    )

    # Clear any previous extraction run for this meeting so re-running
    # extraction doesn't duplicate items.
    db.query(ExtractedItem).filter(ExtractedItem.meeting_id == meeting.id).delete()

    created: list[ExtractedItem] = []

    # --- Requirements & Decisions agent ---
    req_dec_result = RequirementsDecisionsAgent().extract(transcript_block)

    for req in req_dec_result.requirements:
        created.append(
            _build_item(
                db, meeting.id, "requirement", "requirements_decisions_agent",
                req.text, req.evidence.segment_id, req.confidence, baseline,
            )
        )

    for dec in req_dec_result.decisions:
        created.append(
            _build_item(
                db, meeting.id, "decision", "requirements_decisions_agent",
                dec.text, dec.evidence.segment_id, dec.confidence, baseline,
            )
        )

    # --- Action Items & Ownership agent ---
    action_result = ActionItemsAgent().extract(transcript_block)

    for item in action_result.action_items:
        created.append(
            _build_item(
                db, meeting.id, "action_item", "action_items_agent",
                item.text, item.evidence.segment_id, item.confidence, baseline,
                owner=item.owner, due_date=item.due_date,
            )
        )

    # --- Risks / Open Questions agent ---
    risks_result = RisksAgent().extract(transcript_block)

    for item in risks_result.items:
        created.append(
            _build_item(
                db, meeting.id, item.category, "risks_agent",
                item.text, item.evidence.segment_id, item.confidence, baseline,
            )
        )

    db.add_all(created)
    db.commit()

    for item in created:
        db.refresh(item)

    return created


def _build_item(
    db: Session,
    meeting_id: uuid.UUID,
    item_type: str,
    agent_name: str,
    text: str,
    segment_id: str | None,
    extraction_confidence: float,
    baseline: float,
    owner: str | None = None,
    due_date: str | None = None,
) -> ExtractedItem:
    evidence = _resolve_evidence(db, meeting_id, segment_id)

    return ExtractedItem(
        meeting_id=meeting_id,
        item_type=item_type,
        agent_name=agent_name,
        text=text,
        owner=owner,
        due_date=due_date,
        segment_id=evidence.segment_id if evidence else None,
        evidence_speaker=evidence.speaker if evidence else None,
        evidence_timestamp=evidence.timestamp if evidence else None,
        evidence_text=evidence.text if evidence else None,
        extraction_confidence=extraction_confidence,
        source_baseline_confidence=baseline,
        combined_confidence=_combined_confidence(baseline, extraction_confidence),
        review_status="pending",
    )