from app.schemas.evidence import VerifiedEvidence
from app.services.meeting_intelligence import (
    VerifiedExtractedItem,
    VerifiedExtractionResult,
)


def test_verified_extracted_item():
    """
    Test that a verified extracted requirement can be created
    with valid evidence and confidence.
    """

    evidence = VerifiedEvidence(
        segment_id="SEG-0001",
        speaker="Sarah",
        timestamp="00:10:15",
        text="The application must support OTP-based login.",
        source_line_start=1,
        source_line_end=2,
    )

    item = VerifiedExtractedItem(
        text="The application must support OTP-based login.",
        evidence=evidence,
        confidence=0.95,
    )

    assert item.text == (
        "The application must support OTP-based login."
    )

    assert item.evidence.segment_id == "SEG-0001"
    assert item.evidence.speaker == "Sarah"
    assert item.evidence.timestamp == "00:10:15"

    assert item.evidence.text == (
        "The application must support OTP-based login."
    )

    assert item.confidence == 0.95


def test_verified_extraction_result():
    """
    Test that requirements and decisions can be stored
    in a VerifiedExtractionResult.
    """

    requirement_evidence = VerifiedEvidence(
        segment_id="SEG-0001",
        speaker="Sarah",
        timestamp="00:10:15",
        text="The application must support OTP-based login.",
        source_line_start=1,
        source_line_end=2,
    )

    decision_evidence = VerifiedEvidence(
        segment_id="SEG-0002",
        speaker="John",
        timestamp="00:11:30",
        text="We will use SMS for the initial release.",
        source_line_start=3,
        source_line_end=4,
    )

    requirement = VerifiedExtractedItem(
        text="The application must support OTP-based login.",
        evidence=requirement_evidence,
        confidence=0.95,
    )

    decision = VerifiedExtractedItem(
        text="Use SMS for the initial release.",
        evidence=decision_evidence,
        confidence=0.92,
    )

    result = VerifiedExtractionResult(
        requirements=[requirement],
        decisions=[decision],
    )

    assert len(result.requirements) == 1
    assert len(result.decisions) == 1

    assert (
        result.requirements[0].text
        == "The application must support OTP-based login."
    )

    assert (
        result.requirements[0].evidence.speaker
        == "Sarah"
    )

    assert (
        result.requirements[0].evidence.timestamp
        == "00:10:15"
    )

    assert (
        result.decisions[0].text
        == "Use SMS for the initial release."
    )

    assert (
        result.decisions[0].evidence.speaker
        == "John"
    )


def test_empty_verified_extraction_result():
    """
    Test that an empty result is valid.
    """

    result = VerifiedExtractionResult()

    assert result.requirements == []
    assert result.decisions == []


def test_confidence_must_be_between_zero_and_one():
    """
    Test that confidence values outside 0.0-1.0 are rejected.
    """

    evidence = VerifiedEvidence(
        segment_id="SEG-0001",
        speaker="Sarah",
        timestamp="00:10:15",
        text="Test evidence.",
        source_line_start=1,
        source_line_end=1,
    )

    try:
        VerifiedExtractedItem(
            text="Test requirement.",
            evidence=evidence,
            confidence=1.5,
        )

        assert False, (
            "Expected validation error for confidence > 1.0"
        )

    except ValueError:
        pass


def test_evidence_contains_authoritative_metadata():
    """
    Verify that evidence contains the metadata that will
    eventually be used for traceability in the MOM.
    """

    evidence = VerifiedEvidence(
        segment_id="SEG-0024",
        speaker="Ravi Kumar(SS)",
        timestamp="14:55",
        text=(
            "On the six points, sir, IP and coordination "
            "of DDG, we are waiting for the SRS, sir."
        ),
        source_line_start=20,
        source_line_end=22,
    )

    assert evidence.segment_id == "SEG-0024"
    assert evidence.speaker == "Ravi Kumar(SS)"
    assert evidence.timestamp == "14:55"

    assert evidence.source_line_start == 20
    assert evidence.source_line_end == 22

    assert evidence.text.startswith(
        "On the six points"
    )