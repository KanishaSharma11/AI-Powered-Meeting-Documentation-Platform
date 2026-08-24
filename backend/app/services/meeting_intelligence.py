from pydantic import BaseModel, Field

from app.schemas.evidence import VerifiedEvidence


class VerifiedExtractedItem(BaseModel):
    """
    An AI-extracted requirement or decision enriched with
    application-verified transcript evidence.

    The text and confidence come from the AI extraction,
    while the evidence is resolved and verified by the
    application against the normalized transcript.
    """

    text: str = Field(
        description=(
            "The requirement or decision extracted from "
            "the meeting."
        )
    )

    evidence: VerifiedEvidence = Field(
        description=(
            "Verified evidence resolved from the normalized "
            "transcript."
        )
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Confidence that the requirement or decision "
            "was correctly extracted from the evidence."
        )
    )


class VerifiedExtractionResult(BaseModel):
    """
    Complete evidence-verified meeting intelligence.

    Contains the requirements and decisions extracted from
    the meeting and enriched with verified transcript evidence.
    """

    requirements: list[VerifiedExtractedItem] = Field(
        default_factory=list,
        description=(
            "Requirements extracted from the meeting with "
            "verified transcript evidence."
        )
    )

    decisions: list[VerifiedExtractedItem] = Field(
        default_factory=list,
        description=(
            "Decisions extracted from the meeting with "
            "verified transcript evidence."
        )
    )