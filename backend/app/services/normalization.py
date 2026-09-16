from app.schemas.transcript import NormalizedTranscript, TranscriptSegment
from app.services.normalization_service import TranscriptNormalizationService

_service = TranscriptNormalizationService()

def normalize_transcript(raw_text: str) -> NormalizedTranscript:
    return _service.normalize(raw_text)

def render_segments_for_prompt(segments) -> str:
    """
    Renders segments into the block format extraction prompts expect.

    Accepts EITHER the Pydantic TranscriptSegment schema (attribute
    timestamp_start, produced by normalize_transcript) OR a real
    database TranscriptSegment ORM row (attribute timestamp) — several
    callers pass DB rows directly (e.g. document_generator_service.py's
    dynamic_custom extraction), so this must not assume one shape.
    """
    blocks = []
    for seg in segments:
        timestamp = getattr(seg, "timestamp_start", None) or getattr(seg, "timestamp", None) or "N/A"
        blocks.append(
            "SEGMENT ID: {sid}\nSPEAKER: {speaker}\nTIMESTAMP: {ts}\nTEXT: {text}".format(
                sid=seg.segment_id, speaker=seg.speaker or "Unknown",
                ts=timestamp, text=seg.text,
            )
        )
    return "\n\n".join(blocks)