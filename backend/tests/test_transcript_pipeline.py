import pytest

from app.schemas.transcript import (
    NormalizedTranscript,
    TranscriptSegment,
)
from app.services.normalization_service import (
    TranscriptNormalizationService,
)
from app.services.evidence_service import (
    EvidenceService,
)


# ============================================================
# TEST 1
# Full normalization of the actual transcript-style format
# ============================================================

def test_full_transcript_normalization():
    transcript = """\
Shyam Jagannathan   11:47
Ravi, sir, good afternoon.

Ravi Kumar(SS)   11:49
Yes, sir, good afternoon.

Coastal   11:52
We are waiting for the SRS document.

Sarah   12:01
The application must support OTP-based login.
"""

    normalizer = TranscriptNormalizationService()

    result = normalizer.normalize(transcript)

    # --------------------------------------------------------
    # Basic result validation
    # --------------------------------------------------------

    assert isinstance(result, NormalizedTranscript)

    assert result.original_text == transcript

    assert len(result.segments) == 4

    # --------------------------------------------------------
    # Segment IDs
    # --------------------------------------------------------

    assert [
        segment.segment_id
        for segment in result.segments
    ] == [
        "SEG-0001",
        "SEG-0002",
        "SEG-0003",
        "SEG-0004",
    ]

    # --------------------------------------------------------
    # SEG-0001
    # --------------------------------------------------------

    segment = result.segments[0]

    assert segment.segment_id == "SEG-0001"
    assert segment.speaker == "Shyam Jagannathan"
    assert segment.timestamp_start == "11:47"
    assert segment.timestamp_end is None
    assert segment.text == "Ravi, sir, good afternoon."

    # --------------------------------------------------------
    # SEG-0002
    # --------------------------------------------------------

    segment = result.segments[1]

    assert segment.segment_id == "SEG-0002"
    assert segment.speaker == "Ravi Kumar(SS)"
    assert segment.timestamp_start == "11:49"
    assert segment.timestamp_end is None
    assert segment.text == "Yes, sir, good afternoon."

    # --------------------------------------------------------
    # SEG-0003
    # --------------------------------------------------------

    segment = result.segments[2]

    assert segment.segment_id == "SEG-0003"
    assert segment.speaker == "Coastal"
    assert segment.timestamp_start == "11:52"
    assert segment.text == (
        "We are waiting for the SRS document."
    )

    # --------------------------------------------------------
    # SEG-0004
    # --------------------------------------------------------

    segment = result.segments[3]

    assert segment.segment_id == "SEG-0004"
    assert segment.speaker == "Sarah"
    assert segment.timestamp_start == "12:01"
    assert segment.text == (
        "The application must support OTP-based login."
    )


# ============================================================
# TEST 2
# Verify continuation lines are attached to the correct
# speaker segment.
# ============================================================

def test_multiline_speaker_segment():
    transcript = """\
Ravi Kumar(SS)   11:49
Yes, sir, good afternoon.
We have completed the first phase.
We are now waiting for the SRS.
"""

    normalizer = TranscriptNormalizationService()

    result = normalizer.normalize(transcript)

    assert len(result.segments) == 1

    segment = result.segments[0]

    assert segment.segment_id == "SEG-0001"
    assert segment.speaker == "Ravi Kumar(SS)"
    assert segment.timestamp_start == "11:49"

    assert segment.text == (
        "Yes, sir, good afternoon. "
        "We have completed the first phase. "
        "We are now waiting for the SRS."
    )

    assert segment.source_line_start == 1
    assert segment.source_line_end == 4


# ============================================================
# TEST 3
# Verify different transcript formats.
# ============================================================

@pytest.mark.parametrize(
    "transcript, expected_speaker, expected_timestamp, expected_text",
    [
        (
            "[00:10:15] Sarah: Hello everyone.",
            "Sarah",
            "00:10:15",
            "Hello everyone.",
        ),
        (
            "Sarah (00:10:15): Hello everyone.",
            "Sarah",
            "00:10:15",
            "Hello everyone.",
        ),
        (
            "00:10:15 - Sarah: Hello everyone.",
            "Sarah",
            "00:10:15",
            "Hello everyone.",
        ),
        (
            "Sarah: Hello everyone.",
            "Sarah",
            None,
            "Hello everyone.",
        ),
    ],
)
def test_supported_transcript_formats(
    transcript,
    expected_speaker,
    expected_timestamp,
    expected_text,
):
    normalizer = TranscriptNormalizationService()

    result = normalizer.normalize(transcript)

    assert len(result.segments) == 1

    segment = result.segments[0]

    assert segment.segment_id == "SEG-0001"
    assert segment.speaker == expected_speaker
    assert segment.timestamp_start == expected_timestamp
    assert segment.text == expected_text


# ============================================================
# TEST 4
# Verify source line tracking.
# ============================================================
def test_source_line_tracking():
    transcript = """\
Ravi Kumar(SS)   11:49
Yes, sir.

This is a continuation.

Sarah   12:00
Good morning.
"""

    normalizer = TranscriptNormalizationService()

    result = normalizer.normalize(transcript)

    assert len(result.segments) == 2

    first = result.segments[0]

    assert first.segment_id == "SEG-0001"
    assert first.source_line_start == 1
    assert first.source_line_end == 4

    second = result.segments[1]

    assert second.segment_id == "SEG-0002"
    assert second.source_line_start == 6
    assert second.source_line_end == 7
    
# ============================================================
# TEST 5
# Verify empty transcripts are rejected.
# ============================================================

def test_empty_transcript_rejected():
    normalizer = TranscriptNormalizationService()

    with pytest.raises(
        ValueError,
        match="Transcript cannot be empty",
    ):
        normalizer.normalize("")


# ============================================================
# TEST 6
# Verify whitespace-only transcripts are rejected.
# ============================================================

def test_whitespace_transcript_rejected():
    normalizer = TranscriptNormalizationService()

    with pytest.raises(
        ValueError,
        match="Transcript cannot be empty",
    ):
        normalizer.normalize("   \n   \n   ")


# ============================================================
# TEST 7
# Verify EvidenceService can resolve a normalized segment.
# ============================================================

def test_evidence_resolution():
    transcript = """\
Shyam Jagannathan   11:47
Ravi, sir, good afternoon.

Ravi Kumar(SS)   11:49
Yes, sir, good afternoon.
"""

    normalizer = TranscriptNormalizationService()

    normalized = normalizer.normalize(transcript)

    evidence_service = EvidenceService()

    evidence = evidence_service.resolve(
        segment_id="SEG-0002",
        transcript=normalized,
    )

    # --------------------------------------------------------
    # Evidence identity
    # --------------------------------------------------------

    assert evidence.segment_id == "SEG-0002"

    # --------------------------------------------------------
    # Evidence metadata
    # --------------------------------------------------------

    assert evidence.speaker == "Ravi Kumar(SS)"

    assert evidence.timestamp == "11:49"

    # --------------------------------------------------------
    # Exact transcript text
    # --------------------------------------------------------

    assert evidence.text == (
        "Yes, sir, good afternoon."
    )

    # --------------------------------------------------------
    # Source location
    # --------------------------------------------------------

    assert evidence.source_line_start == 4
    assert evidence.source_line_end == 5


# ============================================================
# TEST 8
# Verify EvidenceService rejects an invalid segment ID.
# ============================================================

def test_invalid_segment_id_rejected():
    transcript = """\
Sarah   10:00
Hello everyone.
"""

    normalizer = TranscriptNormalizationService()

    normalized = normalizer.normalize(transcript)

    evidence_service = EvidenceService()

    with pytest.raises(
        ValueError,
        match="was not found in the normalized transcript",
    ):
        evidence_service.resolve(
            segment_id="SEG-9999",
            transcript=normalized,
        )


# ============================================================
# TEST 9
# Verify the evidence text is authoritative.
#
# This confirms that EvidenceService retrieves the text
# from the transcript rather than accepting arbitrary text.
# ============================================================

def test_evidence_uses_authoritative_transcript_text():
    transcript = """\
Ravi Kumar(SS)   11:49
The SRS document is still pending.
"""

    normalizer = TranscriptNormalizationService()

    normalized = normalizer.normalize(transcript)

    evidence_service = EvidenceService()

    evidence = evidence_service.resolve(
        segment_id="SEG-0001",
        transcript=normalized,
    )

    assert evidence.text == (
        "The SRS document is still pending."
    )

    assert evidence.text != (
        "The SRS document has been completed."
    )


# ============================================================
# TEST 10
# Full end-to-end normalization → evidence flow.
#
# This is the most important test in this file.
# ============================================================

def test_full_evidence_backed_pipeline():
    transcript = """\
Shyam Jagannathan   11:47
Ravi, sir, good afternoon.

Ravi Kumar(SS)   11:49
Yes, sir, good afternoon.

Coastal   11:52
We are waiting for the SRS document.

Sarah   12:01
The application must support OTP-based login.
"""

    # --------------------------------------------------------
    # STEP 1 — Normalize transcript
    # --------------------------------------------------------

    normalizer = TranscriptNormalizationService()

    normalized = normalizer.normalize(transcript)

    assert isinstance(
        normalized,
        NormalizedTranscript,
    )

    assert len(normalized.segments) == 4

    # --------------------------------------------------------
    # STEP 2 — Verify generated segment IDs
    # --------------------------------------------------------

    segment_ids = [
        segment.segment_id
        for segment in normalized.segments
    ]

    assert segment_ids == [
        "SEG-0001",
        "SEG-0002",
        "SEG-0003",
        "SEG-0004",
    ]

    # --------------------------------------------------------
    # STEP 3 — Simulate what the AI would return.
    #
    # IMPORTANT:
    #
    # The AI only needs to identify the segment ID.
    # It does NOT provide speaker/timestamp/text.
    # --------------------------------------------------------

    ai_selected_segment_ids = [
        "SEG-0003",
        "SEG-0004",
    ]

    # --------------------------------------------------------
    # STEP 4 — Resolve AI-selected evidence
    # --------------------------------------------------------

    evidence_service = EvidenceService()

    verified_evidence = []

    for segment_id in ai_selected_segment_ids:

        evidence = evidence_service.resolve(
            segment_id=segment_id,
            transcript=normalized,
        )

        verified_evidence.append(evidence)

    # --------------------------------------------------------
    # STEP 5 — Verify evidence
    # --------------------------------------------------------

    assert len(verified_evidence) == 2

    # First evidence
    assert verified_evidence[0].segment_id == "SEG-0003"
    assert verified_evidence[0].speaker == "Coastal"
    assert verified_evidence[0].timestamp == "11:52"
    assert verified_evidence[0].text == (
        "We are waiting for the SRS document."
    )

    # Second evidence
    assert verified_evidence[1].segment_id == "SEG-0004"
    assert verified_evidence[1].speaker == "Sarah"
    assert verified_evidence[1].timestamp == "12:01"
    assert verified_evidence[1].text == (
        "The application must support OTP-based login."
    )

    # --------------------------------------------------------
    # STEP 6 — Verify source locations
    # --------------------------------------------------------

    assert (
        verified_evidence[0].source_line_start == 7
    )

    assert (
        verified_evidence[0].source_line_end == 8
    )

    assert (
        verified_evidence[1].source_line_start == 10
    )

    assert (
        verified_evidence[1].source_line_end == 11
    )