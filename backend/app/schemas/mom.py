from pydantic import BaseModel, Field


class MOMRequirement(BaseModel):
    """
    A requirement displayed in the generated MOM.

    Evidence is deliberately NOT included in this model.
    Evidence is maintained separately in the verified
    intelligence layer and will later be accessible
    through the meeting evidence chat.
    """

    text: str = Field(
        description=(
            "Requirement displayed in the Minutes of Meeting."
        )
    )


class MOMDecision(BaseModel):
    """
    A decision displayed in the generated MOM.

    Evidence is deliberately NOT included in this model.
    """

    text: str = Field(
        description=(
            "Decision displayed in the Minutes of Meeting."
        )
    )


class MOMDocument(BaseModel):
    """
    Clean, human-readable Minutes of Meeting.

    This model intentionally contains no evidence metadata.

    Evidence remains available internally through the
    VerifiedExtractionResult and can later be retrieved
    through the meeting chat system.
    """

    meeting_title: str = Field(
        default="Meeting Minutes",
        description="Title of the meeting.",
    )

    meeting_date: str | None = Field(
        default=None,
        description="Date of the meeting.",
    )

    participants: list[str] = Field(
        default_factory=list,
        description="Participants identified from the meeting.",
    )

    requirements: list[MOMRequirement] = Field(
        default_factory=list,
        description="Requirements included in the MOM.",
    )

    decisions: list[MOMDecision] = Field(
        default_factory=list,
        description="Decisions included in the MOM.",
    )