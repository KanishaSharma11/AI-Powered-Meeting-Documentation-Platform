"""
Knowledge Fusion Engine (Stage 3, Section 2.4).

Runs whenever a human accepts or edits an extracted item belonging to
a meeting that's part of a project. Compares the confirmed text
against the project's existing facts of the same type and either:

  - merges it into an existing fact as a "duplicate" revision, or
  - flags an existing fact as "conflicted" and records both versions
    (never silently overwrites), or
  - creates a brand new ProjectFact.

Only ever touches facts within the SAME project and SAME fact_type —
an "action_item" in Project A never gets compared against a
"requirement" in Project B.
"""

from sqlalchemy.orm import Session

from app.ai.agents.fusion_agent import FusionAgent
from app.models.extraction import ExtractedItem
from app.models.fact import ProjectFact, ProjectFactRevision
from app.models.meeting import Meeting
from app.schemas.fusion import FusionCandidate

# Shared with Stage 4's document generator
# (services/document_generator_service.py) — both need the same
# mapping from raw item_type to fusion/content bucket. Made public
# (no leading underscore) specifically so it can be imported there.
FUSION_TYPE_GROUPS = {
    "requirement": "requirement",
    "decision": "decision",
    "action_item": "action_item",
    "risk": "risk_or_question",
    "blocker": "risk_or_question",
    "open_question": "risk_or_question",
}


def maybe_fuse_item(db: Session, item: ExtractedItem) -> ProjectFact | None:
    """
    Entry point called from the review endpoint after an item is
    accepted or edited. No-ops (returns None) if the item's meeting
    doesn't belong to a project, or the item was already fused once.
    """
    if item.review_status not in ("accepted", "edited"):
        return None
    if item.project_fact_id is not None:
        return None  # already fused on a prior review action

    meeting = db.get(Meeting, item.meeting_id)
    if meeting is None or meeting.project_id is None:
        return None  # standalone meeting, Stage 1/2 behavior — no fusion

    fusion_group = FUSION_TYPE_GROUPS.get(item.item_type)
    if fusion_group is None:
        return None

    candidates = (
        db.query(ProjectFact)
        .filter(
            ProjectFact.project_id == meeting.project_id,
            ProjectFact.fact_type == fusion_group,
        )
        .all()
    )

    candidate_schemas = [
        FusionCandidate(fact_id=str(c.id), text=c.canonical_text) for c in candidates
    ]

    decision = FusionAgent().classify(item.final_text, candidate_schemas)

    if decision.decision == "new" or not candidates:
        return _create_new_fact(db, meeting, item, fusion_group)

    matched = next(
        (c for c in candidates if str(c.id) == decision.matched_fact_id), None
    )
    if matched is None:
        return _create_new_fact(db, meeting, item, fusion_group)

    if decision.decision == "duplicate":
        return _record_duplicate(db, matched, meeting, item)

    if decision.decision == "conflict":
        return _record_conflict(db, matched, meeting, item)

    return _create_new_fact(db, meeting, item, fusion_group)


def _create_new_fact(
    db: Session, meeting: Meeting, item: ExtractedItem, fusion_group: str
) -> ProjectFact:
    fact = ProjectFact(
        project_id=meeting.project_id,
        fact_type=fusion_group,
        canonical_text=item.final_text,
        owner=item.owner,
        due_date=item.due_date,
        status="active",
        confidence=item.combined_confidence,
        first_meeting_id=meeting.id,
        last_meeting_id=meeting.id,
    )
    db.add(fact)
    db.flush()

    db.add(
        ProjectFactRevision(
            fact_id=fact.id,
            meeting_id=meeting.id,
            extracted_item_id=item.id,
            text=item.final_text,
            relation="initial",
            confidence=item.combined_confidence,
        )
    )
    item.project_fact_id = fact.id
    db.commit()
    db.refresh(fact)
    return fact


def _record_duplicate(
    db: Session, fact: ProjectFact, meeting: Meeting, item: ExtractedItem
) -> ProjectFact:
    fact.last_meeting_id = meeting.id
    db.add(
        ProjectFactRevision(
            fact_id=fact.id,
            meeting_id=meeting.id,
            extracted_item_id=item.id,
            text=item.final_text,
            relation="duplicate",
            confidence=item.combined_confidence,
        )
    )
    item.project_fact_id = fact.id
    db.commit()
    db.refresh(fact)
    return fact


def _record_conflict(
    db: Session, fact: ProjectFact, meeting: Meeting, item: ExtractedItem
) -> ProjectFact:
    fact.status = "conflicted"
    fact.last_meeting_id = meeting.id
    db.add(
        ProjectFactRevision(
            fact_id=fact.id,
            meeting_id=meeting.id,
            extracted_item_id=item.id,
            text=item.final_text,
            relation="conflict",
            confidence=item.combined_confidence,
        )
    )
    item.project_fact_id = fact.id
    db.commit()
    db.refresh(fact)
    return fact