"""
Student API endpoints — Phase 2.

GET  /api/v1/students/me                   — Current student profile
GET  /api/v1/students/me/mastery           — All topic mastery records
GET  /api/v1/students/me/mastery/{topic_id} — Single topic mastery
GET  /api/v1/students/me/profile           — Aggregated learner profile
GET  /api/v1/students/me/performance       — Computed performance summary
POST /api/v1/students/me/profile/refresh   — Trigger analytics recomputation
"""
from __future__ import annotations

import logging
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.analytics.engine import (
    compute_performance_features,
    update_learner_profile,
)
from app.knowledge_gap.engine import detect_all_knowledge_gaps
from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.dependencies import require_student
from app.models.models import StudentTopicMastery, Topic, User
from app.repositories import analytics_repository, student_repository
from app.schemas.analytics import (
    LearnerProfileResponse,
    StudentPerformanceSummary,
    TopicMasteryResponse,
)
from app.schemas.common import PaginatedResponse, SuccessResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/students", tags=["Students"])


# ─── Helper ───────────────────────────────────────────────────────────────────

def _mastery_to_response(record: StudentTopicMastery, db: Session) -> dict[str, Any]:
    """Enrich a mastery record with topic title for the response."""
    topic = db.query(Topic).filter(Topic.id == record.topic_id).first()
    return {
        "topic_id": record.topic_id,
        "topic_title": topic.title if topic else None,
        "mastery_score": record.mastery_score,
        "mastery_level": record.mastery_level,
        "confidence": record.confidence,
        "attempts": record.attempts,
        "correct_count": record.correct_count,
        "recent_accuracy": record.recent_accuracy,
        "average_accuracy": record.average_accuracy,
        "last_assessed_at": record.last_assessed_at,
    }


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.get(
    "/me",
    response_model=SuccessResponse[dict],
    summary="Get current student profile",
)
def get_my_profile(
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Return the Student record for the authenticated user."""
    student = student_repository.get_student_by_user_id(db, current_user.id)
    if not student:
        raise NotFoundException("Student profile")

    return {
        "success": True,
        "data": {
            "student_id": str(student.id),
            "user_id": str(student.user_id),
            "full_name": student.full_name,
            "email": current_user.email,
            "grade_level": student.grade_level,
            "learning_preferences": student.learning_preferences,
            "enrolled_at": student.enrolled_at,
        },
    }


@router.get(
    "/me/mastery",
    response_model=PaginatedResponse[TopicMasteryResponse],
    summary="Get all topic mastery records for the authenticated student",
)
def get_my_mastery(
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[Session, Depends(get_db)],
    page: int = 1,
    page_size: int = 50,
) -> dict:
    """Return all topic mastery records, newest assessment first."""
    student = student_repository.get_student_by_user_id(db, current_user.id)
    if not student:
        raise NotFoundException("Student profile")

    records = analytics_repository.list_mastery_records(db, student.id)
    total = len(records)
    offset = (page - 1) * page_size
    page_records = records[offset : offset + page_size]

    return {
        "success": True,
        "data": [TopicMasteryResponse(**_mastery_to_response(r, db)) for r in page_records],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, -(-total // page_size)),
    }


@router.get(
    "/me/mastery/{topic_id}",
    response_model=SuccessResponse[TopicMasteryResponse],
    summary="Get mastery for a specific topic",
)
def get_topic_mastery(
    topic_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Return the mastery record for a specific topic."""
    student = student_repository.get_student_by_user_id(db, current_user.id)
    if not student:
        raise NotFoundException("Student profile")

    record = analytics_repository.get_mastery_record(db, student.id, topic_id)
    if not record:
        raise NotFoundException("Mastery record", f"No mastery record found for topic {topic_id}")

    return {
        "success": True,
        "data": TopicMasteryResponse(**_mastery_to_response(record, db)),
    }


@router.get(
    "/me/profile",
    response_model=SuccessResponse[LearnerProfileResponse],
    summary="Get aggregated learner profile",
)
def get_learner_profile(
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """
    Return the aggregated LearnerProfile for the authenticated student.
    Profile is computed lazily — call POST /me/profile/refresh to force
    recomputation from latest interaction data.
    """
    student = student_repository.get_student_by_user_id(db, current_user.id)
    if not student:
        raise NotFoundException("Student profile")

    profile = analytics_repository.get_or_create_learner_profile(db, student.id)
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


@router.post(
    "/me/profile/refresh",
    response_model=SuccessResponse[LearnerProfileResponse],
    summary="Refresh learner profile from latest interaction data",
)
def refresh_learner_profile(
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """
    Trigger a full recomputation of the learner profile from raw
    quiz attempt, event, and session data. This is an analytics-write
    operation that may take a moment for students with many interactions.
    """
    student = student_repository.get_student_by_user_id(db, current_user.id)
    if not student:
        raise NotFoundException("Student profile")

    profile = update_learner_profile(db, str(student.id))
    detect_all_knowledge_gaps(db, student.id)
    db.commit()
    db.refresh(profile)

    logger.info(
        "Learner profile refreshed and knowledge gaps updated",
        extra={"student_id": str(student.id), "overall_mastery": profile.overall_mastery},
    )
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
        "message": "Learner profile recomputed from latest interaction data",
    }


@router.get(
    "/me/performance",
    response_model=SuccessResponse[StudentPerformanceSummary],
    summary="Get performance summary for the authenticated student",
)
def get_performance_summary(
    current_user: Annotated[User, Depends(require_student)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """
    Return aggregated performance statistics across all topics.
    Derived from StudentTopicMastery and LearnerProfile records.

    NOTE: Stats are descriptive and based on interaction data.
    They are NOT predictions or research-validated metrics.
    """
    student = student_repository.get_student_by_user_id(db, current_user.id)
    if not student:
        raise NotFoundException("Student profile")

    records = analytics_repository.list_mastery_records(db, student.id)
    profile = analytics_repository.get_or_create_learner_profile(db, student.id)
    db.commit()

    started = [r for r in records if r.attempts > 0]
    mastered = [r for r in started if r.mastery_level == "mastered"]
    avg_accuracy = (
        sum(r.average_accuracy for r in started) / len(started) if started else 0.0
    )

    strongest: str | None = None
    weakest: str | None = None
    if started:
        best = max(started, key=lambda r: r.mastery_score)
        worst = min(started, key=lambda r: r.mastery_score)
        t_best = db.query(Topic).filter(Topic.id == best.topic_id).first()
        t_worst = db.query(Topic).filter(Topic.id == worst.topic_id).first()
        strongest = t_best.title if t_best else None
        weakest = t_worst.title if t_worst else None

    total_attempts = sum(r.attempts for r in records)

    return {
        "success": True,
        "data": StudentPerformanceSummary(
            overall_mastery=profile.overall_mastery,
            topics_started=len(started),
            topics_mastered=len(mastered),
            total_quiz_attempts=total_attempts,
            average_accuracy_across_topics=round(avg_accuracy, 4),
            strongest_topic=strongest,
            weakest_topic=weakest,
            current_streak_days=profile.current_streak_days,
            engagement_score=profile.engagement_score,
        ),
    }
