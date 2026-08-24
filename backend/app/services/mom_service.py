from app.services.meeting_intelligence import (
    VerifiedExtractionResult,
)
from app.schemas.mom import (
    MOMDecision,
    MOMDocument,
    MOMRequirement,
)


class MOMService:
    """
    Converts verified meeting intelligence into a clean
    Minutes of Meeting document.

    Important:
        Evidence is NOT copied into the MOM.

    Evidence remains inside the verified intelligence
    layer for later retrieval by the evidence chat system.
    """

    def generate(
        self,
        extraction: VerifiedExtractionResult,
        meeting_title: str = "Meeting Minutes",
        meeting_date: str | None = None,
    ) -> MOMDocument:

        participants = self._extract_participants(
            extraction
        )

        requirements = [
            MOMRequirement(
                text=item.text
            )
            for item in extraction.requirements
        ]

        decisions = [
            MOMDecision(
                text=item.text
            )
            for item in extraction.decisions
        ]

        return MOMDocument(
            meeting_title=meeting_title,
            meeting_date=meeting_date,
            participants=participants,
            requirements=requirements,
            decisions=decisions,
        )

    @staticmethod
    def _extract_participants(
        extraction: VerifiedExtractionResult,
    ) -> list[str]:

        participants = []

        items = (
            extraction.requirements
            + extraction.decisions
        )

        for item in items:

            speaker = item.evidence.speaker

            if not speaker:
                continue

            if speaker not in participants:
                participants.append(speaker)

        return participants