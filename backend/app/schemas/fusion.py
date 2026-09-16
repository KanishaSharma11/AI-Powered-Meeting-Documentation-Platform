from pydantic import BaseModel, Field

class FusionCandidate(BaseModel):
    """One existing project fact shown to the fusion agent for comparison."""
    fact_id: str = Field(description="Exact ID of this candidate fact.")
    text: str = Field(description="The current canonical text of this fact.")

class FusionDecision(BaseModel):
    """The fusion agent's classification of a newly accepted item against a project's existing facts."""
    decision: str = Field(description="One of: 'duplicate', 'conflict', 'new'.")
    matched_fact_id: str | None = Field(default=None, description="Required for duplicate/conflict; must exactly match a provided candidate fact_id. Null for 'new'.")
    reasoning: str = Field(description="One or two sentences explaining the decision.")