from langchain_core.prompts import ChatPromptTemplate

from app.ai.llm import get_llm
from app.ai.prompts.risks import RISKS_SYSTEM_PROMPT
from app.schemas.extraction import RisksExtractionResult


class RisksAgent:
    """
    Extracts risks, blockers, and open questions from a normalized
    transcript. Mirrors RequirementsDecisionsAgent's evidence-by-
    segment-id design (see Section 2.5).
    """

    def __init__(self):
        llm = get_llm()

        self.structured_llm = llm.with_structured_output(RisksExtractionResult)

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", RISKS_SYSTEM_PROMPT),
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

    def extract(self, transcript: str) -> RisksExtractionResult:
        return self.chain.invoke({"transcript": transcript})