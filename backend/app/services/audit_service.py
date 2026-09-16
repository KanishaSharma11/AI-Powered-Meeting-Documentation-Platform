from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.models.user import User


def log_action(db: Session, user: User | None, action: str, resource_type: str, resource_id: str | None = None, meta: dict | None = None) -> None:
    """Fire-and-forget audit write. Commits independently of the
    caller's transaction so an entry is durable even if something
    later in the same request rolls back."""
    db.add(AuditLog(
        user_id=user.id if user else None,
        user_email=user.email if user else None,
        action=action, resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else None,
        meta=meta,
    ))
    db.commit()