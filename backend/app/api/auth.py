from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.database import get_db
from app.database.models import User
from app.errors import AppError
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserOut
from app.utils.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
) -> AuthResponse:
    existing = db.scalar(select(User).where(User.email == data.email.lower()))
    if existing:
        raise AppError("EMAIL_EXISTS", "An account with this email already exists.", 400)

    user = User(
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        full_name=data.full_name.strip(),
        role=data.role,
        phone=data.phone.strip() if data.phone else None,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "name": user.full_name,
    })

    return AuthResponse(token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=AuthResponse)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
) -> AuthResponse:
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if not user or not verify_password(data.password, user.password_hash):
        raise AppError("INVALID_CREDENTIALS", "Incorrect email or password.", 401)

    if not user.is_active:
        raise AppError("ACCOUNT_DISABLED", "Your account has been deactivated.", 403)

    if data.role and user.role != data.role:
        role_label = "Shop Owner" if data.role == "shopowner" else "Customer"
        raise AppError(
            "ROLE_MISMATCH",
            f"This account is registered as a {user.role.title()}, not a {role_label}.",
            403,
        )

    token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "name": user.full_name,
    })

    return AuthResponse(token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def get_me(
    current_user: User = Depends(get_current_user),
) -> UserOut:
    return UserOut.model_validate(current_user)
