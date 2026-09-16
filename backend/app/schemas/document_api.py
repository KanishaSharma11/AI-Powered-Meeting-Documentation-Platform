import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class GeneratedDocumentSummary(BaseModel):
    id: uuid.UUID
    meeting_id: uuid.UUID
    template_id: uuid.UUID
    version: int
    filename: str
    generated_by_email: str | None
    generated_at: datetime
    model_config = ConfigDict(from_attributes=True)