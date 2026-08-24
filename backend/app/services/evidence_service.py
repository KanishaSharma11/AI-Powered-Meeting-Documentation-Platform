from app.schemas.evidence import VerifiedEvidence
from app.schemas.transcript import NormalizedTranscript

class EvidenceService:
    """
    Resolves AI-selected transcript segment IDs against
    the authoritative normalized transcript.
    """

    def resolve(self, segment_id:str, transcript: NormalizedTranscript,)-> VerifiedEvidence:
        for segment in transcript.segments:

            if segment.segment_id == segment_id:
                if not segment.text:
                    raise ValueError(
                        f"Transcript segment {segment_id} "
                        "contains no text."
                    )

                return VerifiedEvidence(
                    segment_id=segment.segment_id,
                    speaker=segment.speaker,
                    timestamp=segment.timestamp_start,
                    text=segment.text,
                    source_line_start=segment.source_line_start,
                    source_line_end=segment.source_line_end,
                )
        raise ValueError(
            f"Transcript segment '{segment_id}' "
            "was not found in the normalized transcript."
        )