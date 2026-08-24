from app.ai.agents.requirements_decisions_agent import (
    RequirementsDecisionsAgent,
)
from app.schemas.extraction import ExtractionResult
from app.schemas.transcript import NormalizedTranscript
from app.services.evidence_service import EvidenceService
from app.services.meeting_intelligence import (
    VerifiedExtractedItem,
    VerifiedExtractionResult,
)


class MeetingExtractionService:
    """
    Coordinates AI extraction and application-side
    evidence verification.

    The AI identifies requirements/decisions and selects
    transcript segment IDs.

    The application then resolves those segment IDs against
    the authoritative normalized transcript.
    """

    def __init__(
        self,
        agent: RequirementsDecisionsAgent | None = None,
        evidence_service: EvidenceService | None = None,
    ):
        self.agent = agent or RequirementsDecisionsAgent()

        self.evidence_service = (
            evidence_service or EvidenceService()
        )

    def extract(
        self,
        transcript: NormalizedTranscript,
    ) -> VerifiedExtractionResult:
        """
        Run AI extraction and resolve all evidence references.
        """

        agent_transcript = (
            self._build_agent_transcript(
                transcript
            )
        )

        extraction_result = self.agent.extract(
            agent_transcript
        )

        return self._verify_extraction(
            extraction_result,
            transcript,
        )

    def _build_agent_transcript(
        self,
        transcript: NormalizedTranscript,
    ) -> str:
        """
        Convert the normalized transcript into the explicit
        segment-based format expected by the AI agent.
        """

        segments = []

        for segment in transcript.segments:

            segments.append(
                "\n".join(
                    [
                        (
                            f"SEGMENT ID: "
                            f"{segment.segment_id}"
                        ),
                        (
                            f"SPEAKER: "
                            f"{segment.speaker or 'Unknown'}"
                        ),
                        (
                            f"TIMESTAMP: "
                            f"{segment.timestamp_start or 'Unknown'}"
                        ),
                        f"TEXT: {segment.text}",
                    ]
                )
            )

        return "\n\n".join(segments)

    def _verify_extraction(
        self,
        extraction_result: ExtractionResult,
        transcript: NormalizedTranscript,
    ) -> VerifiedExtractionResult:
        """
        Resolve AI-selected segment IDs into verified evidence.
        """

        requirements = [
            self._verify_item(
                item,
                transcript,
            )
            for item in extraction_result.requirements
        ]

        decisions = [
            self._verify_item(
                item,
                transcript,
            )
            for item in extraction_result.decisions
        ]

        return VerifiedExtractionResult(
            requirements=requirements,
            decisions=decisions,
        )

    def _verify_item(
        self,
        item,
        transcript: NormalizedTranscript,
    ) -> VerifiedExtractedItem:
        """
        Resolve one AI extraction item against the
        authoritative normalized transcript.
        """

        evidence = self.evidence_service.resolve(
            segment_id=item.evidence.segment_id,
            transcript=transcript,
        )

        return VerifiedExtractedItem(
            text=item.text,
            evidence=evidence,
            confidence=item.confidence,
        )