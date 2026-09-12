from sqlalchemy.orm import Session

from app.ai.agents.template_schema_agent import TemplateSchemaAgent
from app.models.document_template import DocumentTemplate, TemplateSection
from app.schemas.document_template import TemplateSectionInput, VALID_CONTENT_TYPES
from app.services.template_parsing_service import parse_docx_template


def upload_and_classify_template(
    db: Session, file_bytes: bytes, name: str, original_filename: str
) -> DocumentTemplate:
    raw_sections = parse_docx_template(file_bytes)

    if not raw_sections:
        raise ValueError(
            "No headings found in this template — nothing to learn from. "
            "Templates need Word heading styles (Heading 1, Heading 2, ...) "
            "to mark section boundaries."
        )

    classification_inputs = [
        TemplateSectionInput(
            section_index=s.order_index,
            heading_text=s.heading_text,
            heading_level=s.heading_level,
            is_table=s.is_table,
            table_columns=s.table_columns,
            raw_text_preview=s.raw_text[:200],
        )
        for s in raw_sections
    ]

    result = TemplateSchemaAgent().classify(classification_inputs)
    classifications_by_index = {c.section_index: c for c in result.sections}

    template = DocumentTemplate(name=name, original_filename=original_filename)
    db.add(template)
    db.flush()

    for raw in raw_sections:
        classification = classifications_by_index.get(raw.order_index)
        content_type = (
            classification.content_type
            if classification and classification.content_type in VALID_CONTENT_TYPES
            else "custom_text"  # safe fallback: never invent a data type the agent didn't confirm
        )

        # Safety net: dynamic_custom requires a description to guide
        # extraction. If the agent violated its own instructions and
        # omitted one, degrade to custom_text rather than running
        # live extraction with meaningless/empty criteria.
        if content_type == "dynamic_custom" and not (
            classification and classification.custom_description
        ):
            content_type = "custom_text"

        db.add(
            TemplateSection(
                template_id=template.id,
                order_index=raw.order_index,
                heading_text=raw.heading_text,
                heading_level=raw.heading_level,
                content_type=content_type,
                is_table=raw.is_table,
                table_columns=raw.table_columns,
                static_text=raw.raw_text or None,
                custom_description=(
                    classification.custom_description
                    if classification and content_type == "dynamic_custom"
                    else None
                ),
            )
        )

    db.commit()
    db.refresh(template)
    return template