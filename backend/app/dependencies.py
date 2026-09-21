"""
FastAPI dependency injection functions.
Provides: database sessions, current authenticated user, role guards.
"""
from typing import Annotated

from fastapi import Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_token
from app.models import User

# ─── Security Scheme ─────────────────────────────────────────────────────────
_bearer_scheme = HTTPBearer(auto_error=False)


# ─── Token Extraction ────────────────────────────────────────────────────────
def _get_token_payload(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)]
) -> dict:
    """Extract and validate JWT from Authorization header."""
    if credentials is None:
        raise UnauthorizedException("Missing authorization header")
    return decode_token(credentials.credentials)


# ─── Current User ────────────────────────────────────────────────────────────
def get_current_user(
    payload: Annotated[dict, Depends(_get_token_payload)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Returns the authenticated User ORM object.
    Raises UnauthorizedException if token is invalid or user not found.
    """
    if payload.get("type") != "access":
        raise UnauthorizedException("Invalid token type")

    user_id: str = payload.get("sub", "")
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise UnauthorizedException("User not found or deactivated")
    return user


# ─── Role Guards ─────────────────────────────────────────────────────────────
def require_student(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Guard: current user must be a student or admin."""
    if current_user.role not in ("student", "admin"):
        raise ForbiddenException("Student access required")
    return current_user


def require_teacher(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Guard: current user must be a teacher or admin."""
    if current_user.role not in ("teacher", "admin"):
        raise ForbiddenException("Teacher access required")
    return current_user


def require_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Guard: current user must be an admin."""
    if current_user.role != "admin":
        raise ForbiddenException("Admin access required")
    return current_user


# ─── Pagination ──────────────────────────────────────────────────────────────
def pagination_params(page: int = 1, page_size: int = 20) -> dict:
    """Common pagination query parameters."""
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    return {"page": page, "page_size": page_size, "offset": (page - 1) * page_size}
