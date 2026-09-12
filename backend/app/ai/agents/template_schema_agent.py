from langchain_core.prompts import ChatPromptTemplate

from app.ai.llm import get_llm
from app.ai.prompts.template_schema import TEMPLATE_SCHEMA_SYSTEM_PROMPT
from app.schemas.document_template import TemplateSectionInput, TemplateClassificationResult


class TemplateSchemaAgent:
    """
    Classifies every parsed template section into a content_type in a
    single LLM call (Section 2.6: "Template Intelligence Layer").
    """

    def __init__(self):
        llm = get_llm()
        self.structured_llm = llm.with_structured_output(TemplateClassificationResult)

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", TEMPLATE_SCHEMA_SYSTEM_PROMPT),
                (
                    "human",
                    """
                    Classify the following template sections.

                    Sections:

                    {sections_block}
                    """,
                ),
            ]
        )

        self.chain = self.prompt | self.structured_llm

    def classify(
        self, sections: list[TemplateSectionInput]
    ) -> TemplateClassificationResult:
        if not sections:
            return TemplateClassificationResult(sections=[])

        blocks = []
        for s in sections:
            blocks.append(
                "section_index: {idx}\n"
                "heading_text: {heading}\n"
                "heading_level: {level}\n"
                "is_table: {is_table}\n"
                "table_columns: {cols}\n"
                "raw_text_preview: {preview}".format(
                    idx=s.section_index,
                    heading=s.heading_text,
                    level=s.heading_level,
                    is_table=s.is_table,
                    cols=s.table_columns or "N/A",
                    preview=(s.raw_text_preview or "")[:200] or "N/A",
                )
            )
        sections_block = "\n\n".join(blocks)

        return self.chain.invoke({"sections_block": sections_block})