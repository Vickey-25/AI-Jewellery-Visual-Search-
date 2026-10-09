from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import User
from app.errors import AppError
from app.utils.security import decode_access_token


def get_token_from_header(authorization: str | None = Header(None)) -> str | None:
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


def get_current_user(
    token: str | None = Depends(get_token_from_header),
    db: Session = Depends(get_db),
) -> User:
    if not token:
        raise AppError("UNAUTHORIZED", "Authentication required. Please sign in.", 401)
    
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise AppError("INVALID_TOKEN", "Session expired or invalid. Please sign in again.", 401)
    
    user_id = int(payload["sub"])
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise AppError("USER_NOT_FOUND", "User account is disabled or no longer exists.", 401)
    
    return user


def require_shopowner(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "shopowner":
        raise AppError(
            "FORBIDDEN",
            "Access restricted to shop owners only. Please switch to a shop owner account.",
            403,
        )
    return current_user


def get_optional_current_user(
    token: str | None = Depends(get_token_from_header),
    db: Session = Depends(get_db),
) -> User | None:
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None
    try:
        user_id = int(payload["sub"])
        user = db.get(User, user_id)
        return user if user and user.is_active else None
    except Exception:
        return None
