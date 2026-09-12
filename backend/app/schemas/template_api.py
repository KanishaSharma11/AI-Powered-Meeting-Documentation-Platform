import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TemplateSectionOut(BaseModel):
    id: uuid.UUID
    order_index: int
    heading_text: str
    heading_level: int
    content_type: str
    is_table: bool
    table_columns: list[str] | None
    static_text: str | None
    custom_description: str | None

    model_config = ConfigDict(from_attributes=True)


class DocumentTemplateOut(BaseModel):
    id: uuid.UUID
    name: str
    original_filename: str
    sections: list[TemplateSectionOut]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentTemplateSummary(BaseModel):
    id: uuid.UUID
    name: str
    original_filename: str
    section_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)