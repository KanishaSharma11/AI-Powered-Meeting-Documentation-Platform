# Importing all models here ensures they are registered on Base.metadata
# before create_all() (or Alembic) runs. Order matters for models with
# forward-referenced relationships resolved by SQLAlchemy at mapper
# configuration time, but not for table creation itself since
# create_all() topologically sorts by FK dependency regardless.
from app.models.project import Project 
from app.models.meeting import Meeting 
from app.models.transcript import TranscriptSegment  
from app.models.extraction import ExtractedItem  
from app.models.fact import ProjectFact, ProjectFactRevision  
from app.models.document_template import DocumentTemplate, TemplateSection  