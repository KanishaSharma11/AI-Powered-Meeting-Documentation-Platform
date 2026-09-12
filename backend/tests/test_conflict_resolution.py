import uuid

from app.models.extraction import ExtractedItem
from app.models.fact import ProjectFact
from app.schemas.fusion import FusionDecision
from app.services import fusion_service


def _accept_new_item(client, db, meeting_id, segment, text):
    item = ExtractedItem(
        meeting_id=uuid.UUID(meeting_id),
        item_type="requirement",
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
    client.patch(f"/api/extractions/{item.id}", json={"action": "accept"})
    return item


def _create_conflicted_fact(client, db, monkeypatch, project, meeting_in_project):
    meeting_id, segments = meeting_in_project
    _accept_new_item(client, db, meeting_id, segments[0], "OTP will be sent via SMS.")
    fact = db.query(ProjectFact).filter(ProjectFact.project_id == uuid.UUID(project["id"])).first()

    res2 = client.post(
        "/api/transcripts/upload",
        json={"title": "Later", "raw_transcript": "Sarah: x.\nRaj: y.", "project_id": project["id"]},
    )
    meeting2_id = res2.json()["id"]
    import sqlalchemy
    from app.models.transcript import TranscriptSegment
    segs2 = db.execute(
        sqlalchemy.select(TranscriptSegment).filter_by(meeting_id=uuid.UUID(meeting2_id))
    ).scalars().all()

    monkeypatch.setattr(
        fusion_service.FusionAgent,
        "classify",
        lambda self, new_text, candidates: FusionDecision(
            decision="conflict", matched_fact_id=str(fact.id), reasoning="conflict"
        ),
    )
    _accept_new_item(client, db, meeting2_id, segs2[0], "OTP will be sent via email, not SMS.")

    db.refresh(fact)
    return fact


def test_resolve_with_chosen_revision(client, db, monkeypatch, project, meeting_in_project):
    fact = _create_conflicted_fact(client, db, monkeypatch, project, meeting_in_project)
    facts = client.get(f"/api/projects/{project['id']}/facts").json()
    fact_data = facts[0]
    assert fact_data["status"] == "conflicted"
    newer_revision_id = fact_data["revisions"][1]["id"]

    res = client.patch(
        f"/api/projects/{project['id']}/facts/{fact.id}/resolve",
        json={"chosen_revision_id": newer_revision_id},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "active"
    assert body["canonical_text"] == "OTP will be sent via email, not SMS."
    assert len(body["revisions"]) == 3
    assert body["revisions"][-1]["relation"] == "resolution"


def test_resolve_with_custom_text(client, db, monkeypatch, project, meeting_in_project):
    fact = _create_conflicted_fact(client, db, monkeypatch, project, meeting_in_project)

    res = client.patch(
        f"/api/projects/{project['id']}/facts/{fact.id}/resolve",
        json={"custom_text": "OTP delivery method to be finalized with vendor."},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "active"
    assert body["canonical_text"] == "OTP delivery method to be finalized with vendor."


def test_resolve_requires_exactly_one_option(client, db, monkeypatch, project, meeting_in_project):
    fact = _create_conflicted_fact(client, db, monkeypatch, project, meeting_in_project)

    res_neither = client.patch(f"/api/projects/{project['id']}/facts/{fact.id}/resolve", json={})
    assert res_neither.status_code == 400

    facts = client.get(f"/api/projects/{project['id']}/facts").json()
    revision_id = facts[0]["revisions"][0]["id"]
    res_both = client.patch(
        f"/api/projects/{project['id']}/facts/{fact.id}/resolve",
        json={"chosen_revision_id": revision_id, "custom_text": "Something"},
    )
    assert res_both.status_code == 400


def test_resolve_non_conflicted_fact_returns_400(client, db, project, meeting_in_project):
    meeting_id, segments = meeting_in_project
    _accept_new_item(client, db, meeting_id, segments[0], "A clean requirement.")
    fact = db.query(ProjectFact).filter(ProjectFact.project_id == uuid.UUID(project["id"])).first()

    res = client.patch(
        f"/api/projects/{project['id']}/facts/{fact.id}/resolve",
        json={"custom_text": "Doesn't matter."},
    )
    assert res.status_code == 400


def test_resolve_unknown_fact_returns_404(client, project):
    fake_id = "00000000-0000-0000-0000-000000000000"
    res = client.patch(
        f"/api/projects/{project['id']}/facts/{fake_id}/resolve",
        json={"custom_text": "x"},
    )
    assert res.status_code == 404