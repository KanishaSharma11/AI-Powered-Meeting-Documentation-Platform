from pydantic import BaseModel, Field

VALID_CONTENT_TYPES = {
    "requirement",
    "decision",
    "action_item",
    "risk_or_question",
    "participants",
    "custom_text",
    "dynamic_custom",
}


class TemplateSectionInput(BaseModel):
    """One raw parsed section shown to the classification agent."""

    section_index: int
    heading_text: str
    heading_level: int
    is_table: bool
    table_columns: list[str] | None = None
    raw_text_preview: str = Field(
        default="", description="First ~200 chars of any static text under this heading."
    )


class TemplateSectionClassification(BaseModel):
    section_index: int = Field(
        description="Must exactly match the section_index of one input section."
    )
    content_type: str = Field(
        description=(
            "One of: 'requirement', 'decision', 'action_item', "
            "'risk_or_question', 'participants', 'custom_text', "
            "'dynamic_custom'."
        )
    )
    custom_description: str | None = Field(
        default=None,
        description=(
            "Required when content_type is 'dynamic_custom': a clear, "
            "specific natural-language description of what kind of "
            "meeting content belongs in this section, written so it "
            "can guide a search of a meeting transcript (e.g. "
            "'Budget-related figures, costs, or financial concerns "
            "raised in the meeting'). Must be null for every other "
            "content_type."
        ),
    )
    reasoning: str = Field(description="One short sentence explaining the choice.")


class TemplateClassificationResult(BaseModel):
    sections: list[TemplateSectionClassification] = Field(default_factory=list)