"""
Teacher API endpoints — Phase 2.

GET /api/v1/teacher/dashboard          — Class-level summary statistics
GET /api/v1/teacher/students           — Paginated student list with mastery
GET /api/v1/teacher/students/{id}      — Individual student learner profile
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.analytics.engine import compute_class_statistics
from app.core.database import get_db
from app.core.exceptions import ForbiddenException, NotFoundException
from app.dependencies import pagination_params, require_teacher
from app.models.models import Student, StudentEvent, User
from app.repositories import analytics_repository, student_repository
from app.schemas.analytics import (
    LearnerProfileResponse,
    StudentMasterySummary,
    TeacherDashboardResponse,
)
from app.schemas.common import PaginatedResponse, SuccessResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/teacher", tags=["Teacher"])


@router.get(
    "/dashboard",
    response_model=SuccessResponse[TeacherDashboardResponse],
    summary="Get class-level dashboard statistics",
)
def get_teacher_dashboard(
    current_user: Annotated[User, Depends(require_teacher)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """
    Return aggregated class statistics for the teacher dashboard.
    Computed from live StudentTopicMastery and LearnerProfile data.

    NOTE: All stats are descriptive (derived from interaction data).
    """
    # Get all student IDs
    all_students = db.query(Student).all()
    student_ids = [str(s.id) for s in all_students]
    total_students = len(student_ids)

    # Students active in the last 7 days
    cutoff_7d = datetime.now(tz=timezone.utc) - timedelta(days=7)
    active_ids_7d = {
        str(row[0])
        for row in db.query(StudentEvent.student_id)
        .filter(StudentEvent.occurred_at >= cutoff_7d)
        .distinct()
        .all()
    }
    active_students_7d = len(active_ids_7d)

    class_stats = compute_class_statistics(db, student_ids)

    logger.info(
        "Teacher dashboard computed",
        extra={
            "total_students": total_students,
            "at_risk": class_stats["at_risk_count"],
            "teacher_id": str(current_user.id),
        },
    )

    return {
        "success": True,
        "data": TeacherDashboardResponse(
            total_students=total_students,
            active_students_7d=active_students_7d,
            average_class_mastery=class_stats["average_class_mastery"],
            at_risk_count=class_stats["at_risk_count"],
            topics_with_most_gaps=class_stats["topics_with_most_gaps"],
            class_accuracy_by_topic=class_stats["class_accuracy_by_topic"],
        ),
    }


@router.get(
    "/students",
    response_model=PaginatedResponse[StudentMasterySummary],
    summary="Get paginated student list with mastery summaries",
)
def list_students(
    current_user: Annotated[User, Depends(require_teacher)],
    db: Annotated[Session, Depends(get_db)],
    pagination: Annotated[dict, Depends(pagination_params)],
) -> dict:
    """
    Return paginated list of students with their mastery and engagement stats.
    Suitable for the teacher's class overview table.
    """
    total = student_repository.count_students(db)
    students = student_repository.list_students_with_mastery(
        db,
        offset=pagination["offset"],
        limit=pagination["page_size"],
    )

    return {
        "success": True,
        "data": [StudentMasterySummary(**s) for s in students],
        "total": total,
        "page": pagination["page"],
        "page_size": pagination["page_size"],
        "total_pages": max(1, -(-total // pagination["page_size"])),
    }


@router.get(
    "/students/{student_id}",
    response_model=SuccessResponse[LearnerProfileResponse],
    summary="Get individual student learner profile",
)
def get_student_profile(
    student_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_teacher)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """
    Return the full LearnerProfile for a specific student.
    Teachers can inspect any student's profile.
    """
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise NotFoundException("Student")

    profile = analytics_repository.get_or_create_learner_profile(db, str(student.id))
    db.commit()

    return {
        "success": True,
        "data": LearnerProfileResponse(
            student_id=student.id,
            overall_mastery=profile.overall_mastery,
            engagement_score=profile.engagement_score,
            current_streak_days=profile.current_streak_days,
            weak_topics=profile.weak_topics or [],
            strong_topics=profile.strong_topics or [],
            performance_summary=profile.performance_summary or {},
            engagement_metrics=profile.engagement_metrics or {},
            current_learning_path=profile.current_learning_path or [],
            updated_at=profile.updated_at,
        ),
    }
