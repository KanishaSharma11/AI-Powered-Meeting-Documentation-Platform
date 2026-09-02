import uuid

from app.models.extraction import ExtractedItem


def _make_item(db, meeting_id, segment, **overrides):
    item = ExtractedItem(
        meeting_id=uuid.UUID(meeting_id),
        item_type=overrides.get("item_type", "requirement"),
        agent_name=overrides.get("agent_name", "requirements_decisions_agent"),
        text=overrides.get("text", "The system shall support OTP login."),
        owner=overrides.get("owner"),
        due_date=overrides.get("due_date"),
        segment_id=segment.segment_id,
        evidence_speaker=segment.speaker,
        evidence_timestamp=segment.timestamp,
        evidence_text=segment.text,
        extraction_confidence=overrides.get("extraction_confidence", 0.95),
        source_baseline_confidence=overrides.get("source_baseline_confidence", 0.99),
        combined_confidence=overrides.get("combined_confidence", 0.9405),
        review_status="pending",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def test_accept_item(client, db, meeting_with_segments):
    meeting_id, segments = meeting_with_segments
    item = _make_item(db, meeting_id, segments[1])

    res = client.patch(f"/api/extractions/{item.id}", json={"action": "accept"})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["review_status"] == "accepted"
    assert body["final_text"] == item.text


def test_reject_item(client, db, meeting_with_segments):
    meeting_id, segments = meeting_with_segments
    item = _make_item(db, meeting_id, segments[1])

    res = client.patch(f"/api/extractions/{item.id}", json={"action": "reject"})
    assert res.status_code == 200
    assert res.json()["review_status"] == "rejected"


def test_edit_item_requires_text(client, db, meeting_with_segments):
    meeting_id, segments = meeting_with_segments
    item = _make_item(db, meeting_id, segments[1])

    res = client.patch(f"/api/extractions/{item.id}", json={"action": "edit"})
    assert res.status_code == 400


def test_edit_item_success(client, db, meeting_with_segments):
    meeting_id, segments = meeting_with_segments
    item = _make_item(db, meeting_id, segments[1])

    res = client.patch(
        f"/api/extractions/{item.id}",
        json={"action": "edit", "edited_text": "The system must support OTP-based login."},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["review_status"] == "edited"
    assert body["final_text"] == "The system must support OTP-based login."


def test_invalid_action_returns_400(client, db, meeting_with_segments):
    meeting_id, segments = meeting_with_segments
    item = _make_item(db, meeting_id, segments[1])

    res = client.patch(f"/api/extractions/{item.id}", json={"action": "approve"})
    assert res.status_code == 400


def test_review_unknown_item_returns_404(client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    res = client.patch(f"/api/extractions/{fake_id}", json={"action": "accept"})
    assert res.status_code == 404


def test_low_confidence_flag(client, db, meeting_with_segments):
    meeting_id, segments = meeting_with_segments
    # baseline 0.99 * extraction 0.6 = 0.594, below LOW_CONFIDENCE_THRESHOLD (0.75)
    item = _make_item(
        db, meeting_id, segments[1],
        extraction_confidence=0.6, combined_confidence=0.594,
    )

    res = client.get(f"/api/meetings/{meeting_id}/extractions")
    assert res.status_code == 200
    matching = [i for i in res.json() if i["id"] == str(item.id)]
    assert matching[0]["low_confidence"] is True