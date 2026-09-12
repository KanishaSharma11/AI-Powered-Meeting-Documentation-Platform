from pydantic import BaseModel, Field


class FusionCandidate(BaseModel):
    """One existing project fact shown to the fusion agent for comparison."""

    fact_id: str = Field(description="Exact ID of this candidate fact.")
    text: str = Field(description="The current canonical text of this fact.")


class FusionDecision(BaseModel):
    """
    The fusion agent's classification of a newly accepted item against
    a project's existing facts (Section 2.4: duplicate removal +
    conflict detection).
    """

    decision: str = Field(
        description=(
            "One of: 'duplicate' (same meaning as an existing fact, "
            "nothing materially new), 'conflict' (contradicts an "
            "existing fact — e.g. changed decision, incompatible "
            "requirement), or 'new' (not meaningfully related to any "
            "existing fact)."
        )
    )

    matched_fact_id: str | None = Field(
        default=None,
        description=(
            "Required when decision is 'duplicate' or 'conflict' — "
            "must exactly match one of the candidate fact_id values "
            "provided. Must be null when decision is 'new'."
        ),
    )

    reasoning: str = Field(
        description="One or two sentences explaining the decision."
    )