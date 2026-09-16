import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_role
from app.models.fact import ProjectFact, ProjectFactRevision
from app.models.meeting import Meeting
from app.models.project import Project
from app.models.user import User
from app.schemas.api import ProjectCreateRequest, ProjectOut, ProjectFactOut, ResolveConflictRequest
from app.services.audit_service import log_action

router = APIRouter(prefix="/projects", tags=["projects"])


def _to_project_out(project: Project, db: Session) -> ProjectOut:
    count = db.query(Meeting).filter(Meeting.project_id == project.id).count()
    return ProjectOut(id=project.id, name=project.name, description=project.description,
                       meeting_count=count, created_at=project.created_at)


@router.post("", response_model=ProjectOut)
def create_project(
    payload: ProjectCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("reviewer", "admin")),
):
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="name is required.")

    project = Project(name=payload.name.strip(), description=payload.description)
    db.add(project)
    db.commit()
    db.refresh(project)

    log_action(db, user, "create_project", "project", str(project.id), meta={"name": project.name})
    return _to_project_out(project, db)


@router.get("", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return [_to_project_out(p, db) for p in db.query(Project).order_by(Project.created_at.desc()).all()]


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: uuid.UUID, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return _to_project_out(project, db)


@router.get("/{project_id}/facts", response_model=list[ProjectFactOut])
def list_project_facts(project_id: uuid.UUID, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    return (
        db.query(ProjectFact)
        .filter(ProjectFact.project_id == project_id)
        .order_by(ProjectFact.fact_type, ProjectFact.created_at)
        .all()
    )


@router.patch("/{project_id}/facts/{fact_id}/resolve", response_model=ProjectFactOut)
def resolve_conflict(
    project_id: uuid.UUID,
    fact_id: uuid.UUID,
    payload: ResolveConflictRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("reviewer", "admin")),
):
    fact = db.get(ProjectFact, fact_id)
    if not fact or fact.project_id != project_id:
        raise HTTPException(status_code=404, detail="Fact not found in this project.")
    if fact.status != "conflicted":
        raise HTTPException(status_code=400, detail="This fact is not in conflict.")
    if payload.chosen_revision_id and payload.custom_text:
        raise HTTPException(status_code=400, detail="Provide either chosen_revision_id or custom_text, not both.")

    if payload.chosen_revision_id:
        revision = db.get(ProjectFactRevision, payload.chosen_revision_id)
        if not revision or revision.fact_id != fact.id:
            raise HTTPException(status_code=400, detail="chosen_revision_id does not belong to this fact.")
        new_text = revision.text
    elif payload.custom_text and payload.custom_text.strip():
        new_text = payload.custom_text.strip()
    else:
        raise HTTPException(status_code=400, detail="Provide either chosen_revision_id or custom_text.")

    fact.canonical_text = new_text
    fact.status = "active"
    db.add(ProjectFactRevision(
        fact_id=fact.id, meeting_id=fact.last_meeting_id, extracted_item_id=None,
        text=new_text, relation="resolution", confidence=fact.confidence,
    ))
    db.commit()
    db.refresh(fact)

    log_action(db, user, "resolve_conflict", "project_fact", str(fact.id), meta={"new_text": new_text})
    return fact