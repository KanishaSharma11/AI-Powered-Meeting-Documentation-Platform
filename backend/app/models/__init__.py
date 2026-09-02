# Importing all models here ensures they are registered on Base.metadata
# before app.core.database's create_all() (or Alembic) runs.
from app.models.meeting import Meeting 
from app.models.transcript import TranscriptSegment 
from app.models.extraction import ExtractedItem 