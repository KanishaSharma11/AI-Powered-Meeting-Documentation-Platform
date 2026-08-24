from pydantic import BaseModel, Field

class EvidenceReference(BaseModel):
    """
    Reference to the transcript segment supporting
    an extracted requirement or decision.
    """

    segment_id: str = Field(
        description =(
             "Exact ID of the transcript segment supporting this requirement or decision."
        )
    )

class ExtractedItem(BaseModel):
    """
    A requirement or decision identified by the Ollama.
    """

    text: str = Field(
        description =(
            "The requirement or decision expressed clearly and concisely."
        )
    )

    evidence: EvidenceReference = Field(
        description=(
            "Reference to the transcript segment supporting "
            "the extracted item."
        )
    )

    confidence: float = Field(
        ge = 0.0,
        le = 1.0,
        description=("Confidence that the item was correctly extracted from the referenced evidence.")
    )

class ExtractionResult(BaseModel):
    """
    Complete output from the Requirements and Decisions agent.
    """

    requirements: list[ExtractedItem] = Field(
        default_factory = list,
        description = (
            "Functional or non-functional requirements identified in the meeting."
        ),
    )

    decisions: list[ExtractedItem] = Field(
        default_factory = list,
        description = (
            "Decisions explicitly agreed upon during the meeting."
        )
    )