"""
Knowledge Gap API endpoints — Phase 3.
"""
from __future__ import annotations

import logging
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundException, ForbiddenException
from app.dependencies import require_student, require_teacher
from app.models.models import User, Student
from app.repositories import knowledge_gap_repository, student_repository
from app.schemas.common import SuccessResponse
from app.schemas.knowledge_gap import KnowledgeGapResponse, ResolveGapRequest

logger = logging.getLogger(__name__)

# Router for Student endpoints
student_router = APIRouter(prefix="/students/me/knowledge-gaps", tags=["Knowledge Gaps (Student)"])

# Router for Teacher endpoints
teacher_router = APIRouter(prefix="/teacher/students", tags=["Knowledge Gaps (Teacher)"])


@student_router.get(
    "",
    response_model=SuccessResponse[list[KnowledgeGapResponse]],
    summary="Get active knowledge gaps for current student",
)
def get_my_knowledge_gaps(
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    """Return all active knowledge gaps for the authenticated student."""
    student = student_repository.get_student_by_user_id(db, current_user.id)
    if not student:
        raise NotFoundException("Student profile")

    gaps = knowledge_gap_repository.get_active_gaps_for_student(db, student.id)
    return {
        "success": True,
        "data": [KnowledgeGapResponse(**gap) for gap in gaps]
    }


@student_router.post(
    "/{gap_id}/resolve",
    response_model=SuccessResponse[KnowledgeGapResponse],
    summary="Mark a knowledge gap as resolved",
)
def resolve_my_knowledge_gap(
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[Session, Depends(get_db)],
    gap_id: uuid.UUID = Path(...),
    body: ResolveGapRequest | None = None,
) -> dict[str, Any]:
    """Manually resolve a knowledge gap."""
    student = student_repository.get_student_by_user_id(db, current_user.id)
    if not student:
        raise NotFoundException("Student profile")

    gap = knowledge_gap_repository.get_gap_by_id(db, gap_id)
    if not gap:
        raise NotFoundException("Knowledge Gap")
    
    # Ensure it belongs to the current student
    if str(gap.student_id) != str(student.id):
        raise ForbiddenException("Cannot resolve another student's knowledge gap")

    if not gap.is_active:
        return {
            "success": True,
            "data": KnowledgeGapResponse.model_validate(gap),
            "message": "Gap was already resolved"
        }

    resolved_gap = knowledge_gap_repository.resolve_knowledge_gap(db, gap)
    db.commit()

    return {
        "success": True,
        "data": KnowledgeGapResponse.model_validate(resolved_gap),
        "message": "Knowledge gap resolved successfully"
    }


@teacher_router.get(
    "/{student_id}/knowledge-gaps",
    response_model=SuccessResponse[list[KnowledgeGapResponse]],
    summary="Get active knowledge gaps for a specific student",
)
def get_student_knowledge_gaps(
    current_user: Annotated[User, Depends(require_teacher)],
    db: Annotated[Session, Depends(get_db)],
    student_id: uuid.UUID = Path(...),
) -> dict[str, Any]:
    """Return active knowledge gaps for a specific student. Teacher only."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise NotFoundException("Student profile")

    gaps = knowledge_gap_repository.get_active_gaps_for_student(db, student.id)
    return {
        "success": True,
        "data": [KnowledgeGapResponse(**gap) for gap in gaps]
    }
