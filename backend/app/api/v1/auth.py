"""
Authentication API endpoints.
Handles register, login, token refresh, and logout.
"""
from typing import Annotated
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import User, Student, Teacher
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.common import SuccessResponse

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=SuccessResponse[TokenResponse], status_code=201)
def register(request: RegisterRequest, db: Annotated[Session, Depends(get_db)]) -> dict:
    """
    Register a new student or teacher account.
    Returns JWT tokens on success.
    """
    # Check email uniqueness
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise ConflictException("A user with this email already exists")

    # Create user
    user = User(
        email=request.email,
        hashed_password=hash_password(request.password),
        role=request.role,
    )
    db.add(user)
    db.flush()  # Get user.id before committing

    # Create role-specific profile
    if request.role == "student":
        student = Student(
            user_id=user.id,
            full_name=request.full_name,
            grade_level=request.grade_level,
        )
        db.add(student)
        db.commit()  # Commit to get both user.id and student.id assigned
        db.refresh(student)
        # Initialize empty learner profile (student.id is now available)
        from app.models import LearnerProfile
        profile = LearnerProfile(student_id=student.id)
        db.add(profile)
        db.commit()
    elif request.role == "teacher":
        teacher = Teacher(user_id=user.id, full_name=request.full_name)
        db.add(teacher)
        db.commit()

    db.refresh(user)

    logger.info("New user registered", extra={"user_id": str(user.id), "role": user.role})

    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id, user.role)

    return {
        "success": True,
        "data": TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            role=user.role,
            user_id=str(user.id),
        ),
        "message": "Registration successful",
    }


@router.post("/login", response_model=SuccessResponse[TokenResponse])
def login(request: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> dict:
    """
    Authenticate with email and password.
    Returns JWT access and refresh tokens.
    """
    user = db.query(User).filter(User.email == request.email, User.is_active == True).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise UnauthorizedException("Invalid email or password")

    # Update last login timestamp
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    logger.info("User logged in", extra={"user_id": str(user.id), "role": user.role})

    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id, user.role)

    return {
        "success": True,
        "data": TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            role=user.role,
            user_id=str(user.id),
        ),
    }


@router.post("/refresh", response_model=SuccessResponse[TokenResponse])
def refresh_token(request: RefreshRequest, db: Annotated[Session, Depends(get_db)]) -> dict:
    """
    Exchange a refresh token for a new access token.
    """
    payload = decode_token(request.refresh_token)
    if payload.get("type") != "refresh":
        raise UnauthorizedException("Invalid token type — must be a refresh token")

    user = db.query(User).filter(User.id == payload["sub"], User.is_active == True).first()
    if not user:
        raise UnauthorizedException("User not found")

    access_token = create_access_token(user.id, user.role)
    new_refresh_token = create_refresh_token(user.id, user.role)

    return {
        "success": True,
        "data": TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            role=user.role,
            user_id=str(user.id),
        ),
    }
