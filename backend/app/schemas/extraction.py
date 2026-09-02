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


class ActionItem(BaseModel):
    """
    A task with an owner, identified by the Action Items & Ownership agent.
    """

    text: str = Field(
        description=(
            "The action item expressed clearly and concisely, "
            "describing what needs to be done."
        )
    )

    owner: str | None = Field(
        default=None,
        description=(
            "The person or role explicitly assigned to this action item. "
            "Use null if no owner was explicitly stated — never guess one."
        ),
    )

    due_date: str | None = Field(
        default=None,
        description=(
            "The due date or timeframe explicitly mentioned for this "
            "action item (e.g. 'next Friday', '2026-09-01'). "
            "Use null if none was stated — never guess one."
        ),
    )

    evidence: EvidenceReference = Field(
        description="Reference to the transcript segment supporting this action item."
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence that the item was correctly extracted from the referenced evidence.",
    )


class ActionItemsExtractionResult(BaseModel):
    """Complete output from the Action Items & Ownership agent."""

    action_items: list[ActionItem] = Field(
        default_factory=list,
        description="Tasks with owners and/or due dates identified in the meeting.",
    )


class RiskOrQuestion(BaseModel):
    """
    A risk, blocker, or unresolved question identified by the
    Risks/Open Questions agent.
    """

    text: str = Field(
        description="The risk, blocker, or open question expressed clearly and concisely."
    )

    category: str = Field(
        description=(
            "One of: 'risk', 'blocker', 'open_question'. "
            "Classify based on how it was raised in the meeting."
        )
    )

    evidence: EvidenceReference = Field(
        description="Reference to the transcript segment supporting this item."
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence that the item was correctly extracted from the referenced evidence.",
    )


class RisksExtractionResult(BaseModel):
    """Complete output from the Risks/Open Questions agent."""

    items: list[RiskOrQuestion] = Field(
        default_factory=list,
        description="Risks, blockers, and open questions identified in the meeting.",
    )