import io
import uuid

from docx import Document

from app.models.extraction import ExtractedItem


def _accepted_item(db, meeting_id, segment, item_type="requirement", **overrides):
    item = ExtractedItem(
        meeting_id=uuid.UUID(meeting_id),
        item_type=item_type,
        agent_name=overrides.get("agent_name", "requirements_decisions_agent"),
        text=overrides.get("text", "The system shall support OTP login."),
        owner=overrides.get("owner"),
        due_date=overrides.get("due_date"),
        segment_id=segment.segment_id,
        evidence_speaker=segment.speaker,
        evidence_timestamp=segment.timestamp,
        evidence_text=segment.text,
        extraction_confidence=0.95,
        source_baseline_confidence=0.99,
        combined_confidence=0.9405,
        review_status="accepted",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def test_download_without_extraction_returns_400(client, meeting_with_segments):
    meeting_id, _ = meeting_with_segments
    res = client.get(f"/api/meetings/{meeting_id}/mom/download")
    assert res.status_code == 400


def test_download_without_approved_items_returns_400(client, db, meeting_with_segments):
    meeting_id, segments = meeting_with_segments
    item = ExtractedItem(
        meeting_id=uuid.UUID(meeting_id),
        item_type="requirement",
        agent_name="requirements_decisions_agent",
        text="Pending item, not yet reviewed.",
        segment_id=segments[0].segment_id,
        extraction_confidence=0.9,
        source_baseline_confidence=0.99,
        combined_confidence=0.891,
        review_status="pending",
    )
    db.add(item)
    db.commit()

    res = client.get(f"/api/meetings/{meeting_id}/mom/download")
    assert res.status_code == 400


def test_download_succeeds_after_acceptance(client, db, meeting_with_segments):
    meeting_id, segments = meeting_with_segments
    _accepted_item(db, meeting_id, segments[1], text="The system shall support OTP login.")
    _accepted_item(
        db, meeting_id, segments[3], item_type="action_item",
        text="Send the API contract.", owner="Raj", due_date="Friday",
    )

    res = client.get(f"/api/meetings/{meeting_id}/mom/download")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert len(res.content) > 1000  # a real docx, not an empty/error body

    doc = Document(io.BytesIO(res.content))
    full_text = "\n".join(p.text for p in doc.paragraphs)
    assert "OTP login" in full_text


def test_preview_only_shows_accepted_and_edited_items(client, db, meeting_with_segments):
    meeting_id, segments = meeting_with_segments
    _accepted_item(db, meeting_id, segments[0], text="Accepted requirement.")

    rejected = ExtractedItem(
        meeting_id=uuid.UUID(meeting_id),
        item_type="requirement",
        agent_name="requirements_decisions_agent",
        text="Rejected requirement — should not appear.",
        segment_id=segments[1].segment_id,
        extraction_confidence=0.5,
        source_baseline_confidence=0.99,
        combined_confidence=0.495,
        review_status="rejected",
    )
    db.add(rejected)
    db.commit()

    res = client.get(f"/api/meetings/{meeting_id}/mom/preview")
    assert res.status_code == 200
    body = res.json()
    texts = [r["text"] for r in body["requirements"]]
    assert "Accepted requirement." in texts
    assert "Rejected requirement — should not appear." not in texts