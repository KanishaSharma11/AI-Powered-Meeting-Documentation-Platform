"""
Speech & Text Normalization (Section 2.2, step 3).

Delegates to TranscriptNormalizationService for the actual parsing —
that class handles far more real-world transcript formats (two-line
Speaker/Timestamp blocks, bracketed/parenthesized timestamps in either
order, dash-separated, continuation lines) than a single-pattern regex
could. This module exists to keep normalize_transcript() as the one
stable entry point everything else (app/api/transcript.py,
app/services/extraction_service.py) already imports.
"""

from app.schemas.transcript import NormalizedTranscript, TranscriptSegment
from app.services.normalization_service import TranscriptNormalizationService

_service = TranscriptNormalizationService()


def normalize_transcript(raw_text: str) -> NormalizedTranscript:
    return _service.normalize(raw_text)


def render_segments_for_prompt(segments: list[TranscriptSegment]) -> str:
    """
    Render normalized segments into the block format the extraction
    prompts expect (see requirements_decisions prompt for the exact
    shape being matched).
    """
    blocks = []
    for seg in segments:
        blocks.append(
            "SEGMENT ID: {sid}\n"
            "SPEAKER: {speaker}\n"
            "TIMESTAMP: {ts}\n"
            "TEXT: {text}".format(
                sid=seg.segment_id,
                speaker=seg.speaker or "Unknown",
                ts=seg.timestamp_start or "N/A",
                text=seg.text,
            )
        )
    return "\n\n".join(blocks)