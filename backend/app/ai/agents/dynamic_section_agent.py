from langchain_core.prompts import ChatPromptTemplate

from app.ai.llm import get_llm
from app.ai.prompts.dynamic_section import DYNAMIC_SECTION_SYSTEM_PROMPT_TEMPLATE
from app.schemas.dynamic_extraction import DynamicSectionExtractionResult


class DynamicSectionAgent:
    """
    Generalizes the platform's fixed extraction agents (Requirements/
    Decisions, Action Items, Risks) into one agent whose extraction
    criteria is a runtime parameter rather than a hardcoded prompt.

    This is what lets a template section the platform has never seen
    before (e.g. "Budget Notes", "Vendor Commitments") still get real,
    evidence-grounded content instead of being forced into one of the
    fixed categories or left as inert boilerplate.
    """

    def __init__(self, criteria: str):
        llm = get_llm()
        self.structured_llm = llm.with_structured_output(DynamicSectionExtractionResult)

        system_prompt = DYNAMIC_SECTION_SYSTEM_PROMPT_TEMPLATE.format(criteria=criteria)

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                (
                    "human",
                    """
                    Analyze the following normalized meeting transcript.

                    Transcript:

                    {transcript}
                    """,
                ),
            ]
        )

        self.chain = self.prompt | self.structured_llm

    def extract(self, transcript: str) -> DynamicSectionExtractionResult:
        return self.chain.invoke({"transcript": transcript})