from pydantic import BaseModel, Field


class MOMRequirement(BaseModel):
    text: str = Field(description="Requirement displayed in the Minutes of Meeting.")


class MOMDecision(BaseModel):
    text: str = Field(description="Decision displayed in the Minutes of Meeting.")


class MOMActionItem(BaseModel):
    text: str
    owner: str | None = None
    due_date: str | None = None


class MOMRiskOrQuestion(BaseModel):
    text: str
    category: str  # risk | blocker | open_question


class MOMDocument(BaseModel):
    """
    Clean, human-readable Minutes of Meeting. No evidence metadata in
    the body — evidence stays queryable via /extractions instead.
    """
    meeting_title: str = Field(default="Meeting Minutes")
    meeting_date: str | None = None
    participants: list[str] = Field(default_factory=list)
    requirements: list[MOMRequirement] = Field(default_factory=list)
    decisions: list[MOMDecision] = Field(default_factory=list)
    action_items: list[MOMActionItem] = Field(default_factory=list)
    risks: list[MOMRiskOrQuestion] = Field(default_factory=list)