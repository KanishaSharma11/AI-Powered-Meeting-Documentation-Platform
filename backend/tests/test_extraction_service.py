import uuid

import pytest

from app.models.extraction import ExtractedItem
from app.models.meeting import Meeting
from app.schemas.extraction import (
    ExtractionResult,
    ExtractedItem as ExtractedItemSchema,
    EvidenceReference,
    ActionItemsExtractionResult,
    ActionItem,
    RisksExtractionResult,
    RiskOrQuestion,
)
from app.services import extraction_service


def _fake_req_dec_result(segment_id):
    return ExtractionResult(
        requirements=[
            ExtractedItemSchema(
                text="The system shall support OTP login.",
                evidence=EvidenceReference(segment_id=segment_id),
                confidence=0.95,
            )
        ],
        decisions=[
            ExtractedItemSchema(
                text="OTP login is approved for launch.",
                evidence=EvidenceReference(segment_id=segment_id),
                confidence=0.9,
            )
        ],
    )


def _fake_action_items_result(segment_id):
    return ActionItemsExtractionResult(
        action_items=[
            ActionItem(
                text="Send the API contract.",
                owner="Raj",
                due_date="Friday",
                evidence=EvidenceReference(segment_id=segment_id),
                confidence=0.88,
            )
        ]
    )


def _fake_risks_result(segment_id):
    return RisksExtractionResult(
        items=[
            RiskOrQuestion(
                text="Vendor API might not be ready in time.",
                category="risk",
                evidence=EvidenceReference(segment_id=segment_id),
                confidence=0.8,
            )
        ]
    )


@pytest.fixture()
def mocked_agents(monkeypatch, meeting_with_segments):
    """Patches all three agent classes to return fixed, evidence-linked results."""
    _, segments = meeting_with_segments
    seg_id = segments[1].segment_id  # some real segment_id from the fixture meeting

    monkeypatch.setattr(
        extraction_service.RequirementsDecisionsAgent,
        "extract",
        lambda self, transcript: _fake_req_dec_result(seg_id),
    )
    monkeypatch.setattr(
        extraction_service.ActionItemsAgent,
        "extract",
        lambda self, transcript: _fake_action_items_result(seg_id),
    )
    monkeypatch.setattr(
        extraction_service.RisksAgent,
        "extract",
        lambda self, transcript: _fake_risks_result(seg_id),
    )
    return seg_id


def test_run_extraction_persists_items_with_resolved_evidence(
    db, meeting_with_segments, mocked_agents
):
    meeting_id, segments = meeting_with_segments
    meeting = db.get(Meeting, uuid.UUID(meeting_id))

    items = extraction_service.run_extraction(db, meeting)

    assert len(items) == 4  # 1 requirement + 1 decision + 1 action item + 1 risk

    requirement = next(i for i in items if i.item_type == "requirement")
    assert requirement.text == "The system shall support OTP login."
    # Evidence must be resolved from the DB, not just echoed from the LLM.
    assert requirement.evidence_speaker == segments[1].speaker
    assert requirement.evidence_text == segments[1].text
    assert requirement.source_baseline_confidence == 0.99
    assert requirement.combined_confidence == round(0.99 * 0.95, 4)

    action_item = next(i for i in items if i.item_type == "action_item")
    assert action_item.owner == "Raj"
    assert action_item.due_date == "Friday"

    risk = next(i for i in items if i.item_type == "risk")
    assert risk.text == "Vendor API might not be ready in time."


def test_run_extraction_raises_when_no_segments(db):
    empty_meeting = Meeting(title="No transcript yet")
    db.add(empty_meeting)
    db.commit()
    db.refresh(empty_meeting)

    with pytest.raises(ValueError):
        extraction_service.run_extraction(db, empty_meeting)


def test_rerunning_extraction_replaces_previous_items(
    db, meeting_with_segments, mocked_agents
):
    meeting_id, _ = meeting_with_segments
    meeting = db.get(Meeting, uuid.UUID(meeting_id))

    extraction_service.run_extraction(db, meeting)
    first_count = (
        db.query(ExtractedItem).filter(ExtractedItem.meeting_id == meeting.id).count()
    )

    extraction_service.run_extraction(db, meeting)
    second_count = (
        db.query(ExtractedItem).filter(ExtractedItem.meeting_id == meeting.id).count()
    )

    assert first_count == 4
    assert second_count == 4  # not 8 — old items were cleared, not appended


def test_extract_endpoint_returns_counts(client, meeting_with_segments, mocked_agents):
    meeting_id, _ = meeting_with_segments

    res = client.post(f"/api/meetings/{meeting_id}/extract")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["requirements_count"] == 1
    assert body["decisions_count"] == 1
    assert body["action_items_count"] == 1
    assert body["risks_count"] == 1
    assert len(body["items"]) == 4


def test_extract_unknown_meeting_returns_404(client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    res = client.post(f"/api/meetings/{fake_id}/extract")
    assert res.status_code == 404