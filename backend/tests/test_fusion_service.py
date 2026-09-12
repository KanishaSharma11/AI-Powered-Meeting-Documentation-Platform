import uuid

import pytest

from app.models.extraction import ExtractedItem
from app.models.fact import ProjectFact
from app.schemas.fusion import FusionDecision
from app.services import fusion_service


def _make_pending_item(db, meeting_id, segment, item_type="requirement", text="A requirement."):
    item = ExtractedItem(
        meeting_id=uuid.UUID(meeting_id),
        item_type=item_type,
        agent_name="requirements_decisions_agent",
        text=text,
        segment_id=segment.segment_id,
        evidence_speaker=segment.speaker,
        evidence_timestamp=segment.timestamp,
        evidence_text=segment.text,
        extraction_confidence=0.9,
        source_baseline_confidence=0.99,
        combined_confidence=0.891,
        review_status="pending",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


# ---------- No project: fusion never runs ----------

def test_fusion_noop_for_standalone_meeting(client, db, meeting_with_segments):
    meeting_id, segments = meeting_with_segments
    item = _make_pending_item(db, meeting_id, segments[0])

    res = client.patch(f"/api/extractions/{item.id}", json={"action": "accept"})
    assert res.status_code == 200
    assert res.json()["project_fact_id"] is None


# ---------- First item in a project: always "new" ----------

def test_first_item_in_project_creates_new_fact(client, db, project, meeting_in_project):
    meeting_id, segments = meeting_in_project
    item = _make_pending_item(db, meeting_id, segments[0], text="The system shall support OTP login.")

    res = client.patch(f"/api/extractions/{item.id}", json={"action": "accept"})
    assert res.status_code == 200
    fact_id = res.json()["project_fact_id"]
    assert fact_id is not None

    facts = client.get(f"/api/projects/{project['id']}/facts").json()
    assert len(facts) == 1
    assert facts[0]["fact_type"] == "requirement"
    assert facts[0]["status"] == "active"
    assert len(facts[0]["revisions"]) == 1
    assert facts[0]["revisions"][0]["relation"] == "initial"


# ---------- Duplicate ----------

def test_duplicate_merges_into_existing_fact(client, db, monkeypatch, project, meeting_in_project):
    meeting_id, segments = meeting_in_project
    first = _make_pending_item(db, meeting_id, segments[0], text="OTP login is required.")
    client.patch(f"/api/extractions/{first.id}", json={"action": "accept"})

    existing_fact = db.query(ProjectFact).filter(ProjectFact.project_id == uuid.UUID(project["id"])).first()

    # Second meeting in the same project restates the same fact.
    res2 = client.post(
        "/api/transcripts/upload",
        json={"title": "Follow-up", "raw_transcript": "Sarah: yes.\nRaj: ok.", "project_id": project["id"]},
    )
    meeting2_id = res2.json()["id"]
    segs2 = db.execute(
        __import__("sqlalchemy").select(type(segments[0])).filter_by(meeting_id=uuid.UUID(meeting2_id))
    ).scalars().all()

    second = _make_pending_item(db, meeting2_id, segs2[0], text="OTP login is still required.")

    monkeypatch.setattr(
        fusion_service.FusionAgent,
        "classify",
        lambda self, new_text, candidates: FusionDecision(
            decision="duplicate", matched_fact_id=str(existing_fact.id), reasoning="Same requirement restated."
        ),
    )

    res = client.patch(f"/api/extractions/{second.id}", json={"action": "accept"})
    assert res.status_code == 200
    assert res.json()["project_fact_id"] == str(existing_fact.id)

    facts = client.get(f"/api/projects/{project['id']}/facts").json()
    assert len(facts) == 1  # merged, not a second fact
    assert facts[0]["status"] == "active"
    assert len(facts[0]["revisions"]) == 2
    assert facts[0]["revisions"][1]["relation"] == "duplicate"
    # canonical_text unchanged by a duplicate
    assert facts[0]["canonical_text"] == "OTP login is required."


# ---------- Conflict ----------

def test_conflict_flags_fact_without_changing_canonical_text(client, db, monkeypatch, project, meeting_in_project):
    meeting_id, segments = meeting_in_project
    first = _make_pending_item(db, meeting_id, segments[0], text="OTP will be sent via SMS.")
    client.patch(f"/api/extractions/{first.id}", json={"action": "accept"})

    existing_fact = db.query(ProjectFact).filter(ProjectFact.project_id == uuid.UUID(project["id"])).first()

    res2 = client.post(
        "/api/transcripts/upload",
        json={"title": "Later meeting", "raw_transcript": "Sarah: change.\nRaj: ok.", "project_id": project["id"]},
    )
    meeting2_id = res2.json()["id"]
    segs2 = db.execute(
        __import__("sqlalchemy").select(type(segments[0])).filter_by(meeting_id=uuid.UUID(meeting2_id))
    ).scalars().all()

    second = _make_pending_item(db, meeting2_id, segs2[0], text="OTP will be sent via email, not SMS.")

    monkeypatch.setattr(
        fusion_service.FusionAgent,
        "classify",
        lambda self, new_text, candidates: FusionDecision(
            decision="conflict", matched_fact_id=str(existing_fact.id), reasoning="Contradicts delivery method."
        ),
    )

    res = client.patch(f"/api/extractions/{second.id}", json={"action": "accept"})
    assert res.status_code == 200

    facts = client.get(f"/api/projects/{project['id']}/facts").json()
    assert len(facts) == 1
    assert facts[0]["status"] == "conflicted"
    # canonical text NOT silently overwritten
    assert facts[0]["canonical_text"] == "OTP will be sent via SMS."
    assert len(facts[0]["revisions"]) == 2
    assert facts[0]["revisions"][1]["relation"] == "conflict"


# ---------- Agent returns a bogus fact id -> falls back to "new" ----------

def test_bogus_matched_fact_id_falls_back_to_new(client, db, monkeypatch, project, meeting_in_project):
    meeting_id, segments = meeting_in_project
    first = _make_pending_item(db, meeting_id, segments[0], text="First fact.")
    client.patch(f"/api/extractions/{first.id}", json={"action": "accept"})

    second = _make_pending_item(db, meeting_id, segments[1], text="Second unrelated fact.")

    monkeypatch.setattr(
        fusion_service.FusionAgent,
        "classify",
        lambda self, new_text, candidates: FusionDecision(
            decision="duplicate", matched_fact_id="00000000-0000-0000-0000-000000000000", reasoning="bogus"
        ),
    )

    res = client.patch(f"/api/extractions/{second.id}", json={"action": "accept"})
    assert res.status_code == 200

    facts = client.get(f"/api/projects/{project['id']}/facts").json()
    assert len(facts) == 2  # did NOT merge into a nonexistent fact


def test_reviewing_same_item_twice_does_not_double_fuse(client, db, project, meeting_in_project):
    meeting_id, segments = meeting_in_project
    item = _make_pending_item(db, meeting_id, segments[0], text="Some fact.")

    client.patch(f"/api/extractions/{item.id}", json={"action": "accept"})
    facts_after_first = client.get(f"/api/projects/{project['id']}/facts").json()

    # Edit the same item again — should NOT create a second fact or revision.
    client.patch(f"/api/extractions/{item.id}", json={"action": "edit", "edited_text": "Some fact, edited."})
    facts_after_second = client.get(f"/api/projects/{project['id']}/facts").json()

    assert len(facts_after_first) == len(facts_after_second) == 1
    assert len(facts_after_second[0]["revisions"]) == 1