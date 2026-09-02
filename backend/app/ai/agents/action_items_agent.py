from langchain_core.prompts import ChatPromptTemplate

from app.ai.llm import get_llm
from app.ai.prompts.action_items import ACTION_ITEMS_SYSTEM_PROMPT
from app.schemas.extraction import ActionItemsExtractionResult


class ActionItemsAgent:
    """
    Extracts action items (task + owner + due date) from a normalized
    transcript. Mirrors RequirementsDecisionsAgent's evidence-by-
    segment-id design (see Section 2.5).
    """

    def __init__(self):
        llm = get_llm()

        self.structured_llm = llm.with_structured_output(ActionItemsExtractionResult)

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", ACTION_ITEMS_SYSTEM_PROMPT),
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

    def extract(self, transcript: str) -> ActionItemsExtractionResult:
        return self.chain.invoke({"transcript": transcript})