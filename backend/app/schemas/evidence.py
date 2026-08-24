from pydantic import BaseModel, Field

class VerifiedEvidence(BaseModel):
    """
    Authoritative evidence resolved from the normalized
    transcript.

    This data comes from our application, not from the LLM.
    """

    segment_id: str
    speaker: str 
    timestamp:str
    text: str
    source_line_start: int
    source_line_end: int

    