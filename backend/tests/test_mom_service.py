from app.schemas.evidence import VerifiedEvidence
from app.services.meeting_intelligence import (
    VerifiedExtractedItem,
    VerifiedExtractionResult,
)
from app.services.mom_service import MOMService


def create_verified_result():

    requirement = VerifiedExtractedItem(
        text=(
            "The application must support OTP-based login."
        ),
        evidence=VerifiedEvidence(
            segment_id="SEG-0001",
            speaker="Sarah",
            timestamp="00:10:15",
            text=(
                "The application must support "
                "OTP-based login."
            ),
            source_line_start=1,
            source_line_end=3,
        ),
        confidence=0.95,
    )

    decision = VerifiedExtractedItem(
        text=(
            "OTP authentication will be mandatory."
        ),
        evidence=VerifiedEvidence(
            segment_id="SEG-0002",
            speaker="John",
            timestamp="00:10:42",
            text=(
                "Agreed. OTP authentication "
                "will be mandatory."
            ),
            source_line_start=5,
            source_line_end=5,
        ),
        confidence=0.95,
    )

    return VerifiedExtractionResult(
        requirements=[
            requirement
        ],
        decisions=[
            decision
        ],
    )


def test_mom_service_generates_document():

    extraction = create_verified_result()

    service = MOMService()

    mom = service.generate(
        extraction=extraction,
        meeting_title="Authentication Meeting",
        meeting_date="2026-08-13",
    )

    assert mom.meeting_title == (
        "Authentication Meeting"
    )

    assert mom.meeting_date == "2026-08-13"

    assert len(mom.requirements) == 1

    assert len(mom.decisions) == 1


def test_mom_does_not_contain_evidence():

    extraction = create_verified_result()

    service = MOMService()

    mom = service.generate(
        extraction=extraction
    )

    requirement = mom.requirements[0]

    decision = mom.decisions[0]

    # MOM contains only clean text.

    assert requirement.text == (
        "The application must support OTP-based login."
    )

    assert decision.text == (
        "OTP authentication will be mandatory."
    )

    # Evidence must NOT exist in the MOM model.

    assert not hasattr(
        requirement,
        "evidence",
    )

    assert not hasattr(
        requirement,
        "segment_id",
    )

    assert not hasattr(
        decision,
        "evidence",
    )

    assert not hasattr(
        decision,
        "segment_id",
    )


def test_participants_are_extracted():

    extraction = create_verified_result()

    service = MOMService()

    mom = service.generate(
        extraction=extraction
    )

    assert mom.participants == [
        "Sarah",
        "John",
    ]