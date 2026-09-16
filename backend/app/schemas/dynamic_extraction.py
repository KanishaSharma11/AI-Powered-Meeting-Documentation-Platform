from pydantic import BaseModel, Field

from app.schemas.extraction import EvidenceReference


class DynamicExtractedItem(BaseModel):
    """
    One item extracted for a template section that doesn't match any
    of the platform's fixed content types. Extraction criteria is
    provided at call time (see DynamicSectionAgent), not hardcoded.
    """
    text: str = Field(description="The extracted item, expressed clearly and concisely.")
    evidence: EvidenceReference = Field(description="Reference to the transcript segment supporting this item.")
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence that this item was correctly extracted and genuinely matches the requested criteria.",
    )


class DynamicSectionExtractionResult(BaseModel):
    items: list[DynamicExtractedItem] = Field(default_factory=list)