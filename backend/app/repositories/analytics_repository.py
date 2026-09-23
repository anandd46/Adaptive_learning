"""
Analytics repository — data access layer for event tracking and mastery queries.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.models import (
    LearnerProfile,
    LearningSession,
    StudentEvent,
    StudentTopicMastery,
    Topic,
)


def _to_uuid(val: str | uuid.UUID) -> uuid.UUID:
    """Coerce str or UUID to uuid.UUID for SQLAlchemy queries."""
    if isinstance(val, uuid.UUID):
        return val
    return uuid.UUID(str(val))


# ─── Events ───────────────────────────────────────────────────────────────────

def create_event(
    db: Session,
    student_id: str | uuid.UUID,
    event_type: str,
    *,
    topic_id: str | uuid.UUID | None = None,
    resource_id: str | uuid.UUID | None = None,
    session_id: str | uuid.UUID | None = None,
    event_data: dict[str, Any] | None = None,
) -> StudentEvent:
    """Persist a new StudentEvent record and return it."""
    event = StudentEvent(
        student_id=_to_uuid(student_id),
        event_type=event_type,
        topic_id=_to_uuid(topic_id) if topic_id else None,
        resource_id=_to_uuid(resource_id) if resource_id else None,
        session_id=_to_uuid(session_id) if session_id else None,
        event_data=event_data or {},
        occurred_at=datetime.now(tz=timezone.utc),
    )
    db.add(event)
    db.flush()
    return event


def list_events(
    db: Session,
    student_id: str | uuid.UUID,
    *,
    offset: int = 0,
    limit: int = 50,
) -> list[StudentEvent]:
    """Return paginated events for a student, newest first."""
    return (
        db.query(StudentEvent)
        .filter(StudentEvent.student_id == _to_uuid(student_id))
        .order_by(StudentEvent.occurred_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def count_events(db: Session, student_id: str | uuid.UUID) -> int:
    """Count total events for a student."""
    return (
        db.query(StudentEvent)
        .filter(StudentEvent.student_id == _to_uuid(student_id))
        .count()
    )


# ─── Sessions ─────────────────────────────────────────────────────────────────

def create_session(
    db: Session,
    student_id: str | uuid.UUID,
    *,
    course_id: str | uuid.UUID | None = None,
    session_type: str = "study",
) -> LearningSession:
    """Create and persist a new LearningSession."""
    session = LearningSession(
        student_id=_to_uuid(student_id),
        course_id=_to_uuid(course_id) if course_id else None,
        session_type=session_type,
        started_at=datetime.now(tz=timezone.utc),
        duration_seconds=0,
    )
    db.add(session)
    db.flush()
    return session


def get_session(
    db: Session, session_id: str | uuid.UUID, student_id: str | uuid.UUID
) -> LearningSession | None:
    """Return a session if it belongs to the given student."""
    return (
        db.query(LearningSession)
        .filter(
            LearningSession.id == _to_uuid(session_id),
            LearningSession.student_id == _to_uuid(student_id),
        )
        .first()
    )


def end_session(
    db: Session,
    session: LearningSession,
    duration_seconds: int | None = None,
) -> LearningSession:
    """Mark a session as ended and update its duration."""
    now = datetime.now(tz=timezone.utc)
    session.ended_at = now
    if duration_seconds is not None:
        session.duration_seconds = duration_seconds
    elif session.started_at:
        # Auto-compute from wall clock
        started = session.started_at
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        session.duration_seconds = max(0, int((now - started).total_seconds()))
    db.flush()
    return session


# ─── Mastery ──────────────────────────────────────────────────────────────────

def get_mastery_record(
    db: Session,
    student_id: str | uuid.UUID,
    topic_id: str | uuid.UUID,
) -> StudentTopicMastery | None:
    """Return the mastery record for a student-topic pair."""
    return (
        db.query(StudentTopicMastery)
        .filter(
            StudentTopicMastery.student_id == _to_uuid(student_id),
            StudentTopicMastery.topic_id == _to_uuid(topic_id),
        )
        .first()
    )


def list_mastery_records(
    db: Session,
    student_id: str | uuid.UUID,
) -> list[StudentTopicMastery]:
    """Return all mastery records for a student, newest assessment first."""
    return (
        db.query(StudentTopicMastery)
        .filter(StudentTopicMastery.student_id == _to_uuid(student_id))
        .order_by(StudentTopicMastery.last_assessed_at.desc())
        .all()
    )


def get_or_create_learner_profile(
    db: Session, student_id: str | uuid.UUID
) -> LearnerProfile:
    """Return existing LearnerProfile or create an empty one."""
    profile = (
        db.query(LearnerProfile)
        .filter(LearnerProfile.student_id == _to_uuid(student_id))
        .first()
    )
    if profile is None:
        profile = LearnerProfile(
            student_id=_to_uuid(student_id),
            overall_mastery=0.0,
            engagement_score=0.0,
            current_streak_days=0,
            weak_topics=[],
            strong_topics=[],
            performance_summary={},
            engagement_metrics={},
            current_learning_path=[],
            recommendation_history=[],
            intervention_history=[],
        )
        db.add(profile)
        db.flush()
    return profile
