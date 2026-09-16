import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, VALID_ROLES
from app.schemas.auth import UserRegisterRequest, UserOut, TokenResponse
from app.services.auth_service import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
def register(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    Bootstrap rule: the very first user ever registered becomes
    "admin" automatically. Every registration after that defaults to
    "viewer" — an admin upgrades people from there. There is no
    "role" field on this public endpoint; nobody can self-assign
    admin/reviewer.
    """
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")

    is_first_user = db.query(User).count() == 0
    role = "admin" if is_first_user else "viewer"

    user = User(email=payload.email, hashed_password=hash_password(payload.password), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    token = create_access_token(subject=user.email, role=user.role)
    return TokenResponse(access_token=token, role=user.role)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.patch("/users/{user_id}/role", response_model=UserOut)
def set_user_role(
    user_id: uuid.UUID,
    new_role: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin-only: promote/demote another user's role."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can change roles.")
    if new_role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"role must be one of: {', '.join(VALID_ROLES)}.")

    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")

    target.role = new_role
    db.commit()
    db.refresh(target)
    return target