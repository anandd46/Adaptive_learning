"""
Auth schemas — request/response models for authentication endpoints.
"""
from pydantic import BaseModel, EmailStr, field_validator
from typing import Literal


class RegisterRequest(BaseModel):
    """Request body for user registration."""
    email: EmailStr
    password: str
    full_name: str
    role: Literal["student", "teacher"] = "student"
    grade_level: str | None = None  # for students

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    """Request body for login."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token pair returned after successful auth."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    user_id: str


class RefreshRequest(BaseModel):
    """Request body for token refresh."""
    refresh_token: str


class UserPublic(BaseModel):
    """Public user data (never expose hashed_password)."""
    id: str
    email: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}
