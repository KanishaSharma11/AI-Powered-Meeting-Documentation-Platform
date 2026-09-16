"""
FastAPI dependencies for authentication and role-based access control
(Section 6.2). Usage on any endpoint:

    @router.post("/projects")
    def create_project(
        payload: ProjectCreateRequest,
        db: Session = Depends(get_db),
        user: User = Depends(require_role("reviewer", "admin")),
    ):
        ...

require_role() returns a dependency that both authenticates (valid
JWT required) and authorizes (role must be in the allowed set) in one
step. get_current_user() alone is enough when an endpoint just needs
"someone logged in", regardless of role (e.g. for audit-logging who
performed a read).
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.services.auth_service import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token is None:
        raise credentials_exception

    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise credentials_exception

    user = db.query(User).filter(User.email == payload["sub"]).first()
    if user is None:
        raise credentials_exception

    return user


def require_role(*allowed_roles: str):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(allowed_roles)}.",
            )
        return user

    return dependency


def get_optional_current_user(
    token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User | None:
    """For endpoints that behave the same for everyone but still want
    to log WHO did it when a token happens to be present (e.g. a
    public download endpoint you still want attributed when possible)."""
    if token is None:
        return None
    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        return None
    return db.query(User).filter(User.email == payload["sub"]).first()