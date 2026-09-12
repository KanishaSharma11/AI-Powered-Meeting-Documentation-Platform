from langchain_core.prompts import ChatPromptTemplate

from app.ai.llm import get_llm
from app.ai.prompts.fusion import FUSION_SYSTEM_PROMPT
from app.schemas.fusion import FusionCandidate, FusionDecision


class FusionAgent:
    """
    Classifies a newly confirmed fact against a project's existing
    facts of the same type: duplicate, conflict, or new (Section 2.4).
    """

    def __init__(self):
        llm = get_llm()
        self.structured_llm = llm.with_structured_output(FusionDecision)

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", FUSION_SYSTEM_PROMPT),
                (
                    "human",
                    """
                    NEW FACT:
                    {new_fact_text}

                    EXISTING FACTS:
                    {existing_facts_block}
                    """,
                ),
            ]
        )

        self.chain = self.prompt | self.structured_llm

    def classify(
        self, new_fact_text: str, candidates: list[FusionCandidate]
    ) -> FusionDecision:
        if not candidates:
            # Nothing to compare against — skip the LLM call entirely,
            # this is unambiguously "new".
            return FusionDecision(decision="new", matched_fact_id=None, reasoning="No existing facts of this type in the project yet.")

        existing_facts_block = "\n\n".join(
            f"fact_id: {c.fact_id}\ntext: {c.text}" for c in candidates
        )

        return self.chain.invoke(
            {
                "new_fact_text": new_fact_text,
                "existing_facts_block": existing_facts_block,
            }
        )