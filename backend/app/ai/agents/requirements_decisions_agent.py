from langchain_core.prompts import ChatPromptTemplate

from app.ai.llm import get_llm
from app.ai.prompts.requirements_decisions import REQUIREMENTS_DECISIONS_SYSTEM_PROMPT
from app.schemas.extraction import ExtractionResult


class RequirementsDecisionsAgent:
    def __init__(self):
        llm = get_llm()
        self.structured_llm = llm.with_structured_output(ExtractionResult, method="json_schema")
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", REQUIREMENTS_DECISIONS_SYSTEM_PROMPT),
                (
                    "human",
                    """
                    Analyze the following normalized meeting transcript.

                    Each segment has:

                    SEGMENT ID
                    SPEAKER
                    TIMESTAMP
                    TEXT

                    Transcript:

                    {transcript}
                    """,
                ),
            ]
        )
        self.chain = self.prompt | self.structured_llm

    def extract(self, transcript: str) -> ExtractionResult:
        return self.chain.invoke({"transcript": transcript})