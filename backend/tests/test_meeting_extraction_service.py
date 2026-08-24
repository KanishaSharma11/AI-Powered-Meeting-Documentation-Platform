from app.ai.agents.requirements_decisions_agent import (
    RequirementsDecisionsAgent,
)
from app.services.meeting_extraction_service import (
    MeetingExtractionService,
)
from app.services.evidence_service import EvidenceService
from app.services.normalization_service import (
    TranscriptNormalizationService,
)


def test_full_meeting_extraction_pipeline():
    raw_transcript = """\
Sarah   00:10:15
The application must support OTP-based login
for all external users.

John   00:10:42
Agreed. OTP authentication will be mandatory.

Sarah   00:11:10
We are still discussing whether SMS or email
should be used for the OTP.

John   00:12:00
Let's proceed with SMS for the initial release.
"""

    # ========================================================
    # STEP 1 — Normalize transcript
    # ========================================================

    normalizer = TranscriptNormalizationService()

    normalized = normalizer.normalize(
        raw_transcript
    )

    assert len(normalized.segments) == 4

    assert normalized.segments[0].segment_id == "SEG-0001"
    assert normalized.segments[1].segment_id == "SEG-0002"
    assert normalized.segments[2].segment_id == "SEG-0003"
    assert normalized.segments[3].segment_id == "SEG-0004"

    # ========================================================
    # STEP 2 — Create the extraction service
    # ========================================================

    service = MeetingExtractionService(
        agent=RequirementsDecisionsAgent(),
        evidence_service=EvidenceService(),
    )

    # ========================================================
    # STEP 3 — Run AI extraction + evidence verification
    # ========================================================

    result = service.extract(
        normalized
    )

    # ========================================================
    # STEP 4 — Basic result validation
    # ========================================================

    assert result is not None

    assert len(result.requirements) >= 1

    assert len(result.decisions) >= 1

    # ========================================================
    # STEP 5 — Validate requirements
    # ========================================================

    for requirement in result.requirements:

        assert requirement.text

        assert (
            requirement.confidence >= 0.0
        )

        assert (
            requirement.confidence <= 1.0
        )

        # Evidence has been resolved by our backend.
        assert requirement.evidence.segment_id

        assert requirement.evidence.text

        assert (
            requirement.evidence.speaker
            is not None
        )

        assert (
            requirement.evidence.timestamp
            is not None
        )

        assert (
            requirement.evidence.source_line_start
            is not None
        )

        assert (
            requirement.evidence.source_line_end
            is not None
        )

    # ========================================================
    # STEP 6 — Validate decisions
    # ========================================================

    for decision in result.decisions:

        assert decision.text

        assert (
            decision.confidence >= 0.0
        )

        assert (
            decision.confidence <= 1.0
        )

        assert decision.evidence.segment_id

        assert decision.evidence.text

        assert (
            decision.evidence.speaker
            is not None
        )

        assert (
            decision.evidence.timestamp
            is not None
        )

        assert (
            decision.evidence.source_line_start
            is not None
        )

        assert (
            decision.evidence.source_line_end
            is not None
        )

    # ========================================================
    # STEP 7 — Verify evidence references real segments
    # ========================================================

    normalized_segment_ids = {
        segment.segment_id
        for segment in normalized.segments
    }

    for requirement in result.requirements:

        assert (
            requirement.evidence.segment_id
            in normalized_segment_ids
        )

    for decision in result.decisions:

        assert (
            decision.evidence.segment_id
            in normalized_segment_ids
        )


def test_evidence_metadata_matches_source_transcript():
    raw_transcript = """\
Sarah   00:10:15
The application must support OTP-based login
for all external users.

John   00:10:42
Agreed. OTP authentication will be mandatory.
"""

    normalizer = TranscriptNormalizationService()

    normalized = normalizer.normalize(
        raw_transcript
    )

    evidence_service = EvidenceService()

    evidence = evidence_service.resolve(
        segment_id="SEG-0001",
        transcript=normalized,
    )

    # ========================================================
    # Evidence must come from the source transcript.
    # ========================================================

    assert evidence.segment_id == "SEG-0001"

    assert evidence.speaker == "Sarah"

    assert evidence.timestamp == "00:10:15"

    assert evidence.text == (
        "The application must support OTP-based login "
        "for all external users."
    )

    assert evidence.source_line_start == 1

    assert evidence.source_line_end == 3