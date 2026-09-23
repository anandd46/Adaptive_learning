"""
Student repository — data access layer for student-related queries.
Keeps raw SQL/ORM queries out of route handlers.
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session, joinedload

from app.models.models import Student, Teacher, User, LearnerProfile, StudentTopicMastery


def _to_uuid(val: str | uuid.UUID) -> uuid.UUID:
    """Coerce str or UUID to uuid.UUID (safe for both PostgreSQL and SQLite)."""
    if isinstance(val, uuid.UUID):
        return val
    return uuid.UUID(str(val))


def get_student_by_user_id(db: Session, user_id: str | uuid.UUID) -> Student | None:
    """Return the Student profile linked to a User id, or None."""
    return (
        db.query(Student)
        .filter(Student.user_id == _to_uuid(user_id))
        .first()
    )


def get_teacher_by_user_id(db: Session, user_id: str | uuid.UUID) -> Teacher | None:
    """Return the Teacher profile linked to a User id, or None."""
    return (
        db.query(Teacher)
        .filter(Teacher.user_id == _to_uuid(user_id))
        .first()
    )


def get_student_with_profile(
    db: Session, student_id: str | uuid.UUID
) -> Student | None:
    """Return Student with eagerly loaded LearnerProfile."""
    return (
        db.query(Student)
        .options(joinedload(Student.learner_profile))
        .filter(Student.id == str(student_id))
        .first()
    )


def get_student_with_user(
    db: Session, student_id: str | uuid.UUID
) -> tuple[Student, User] | None:
    """Return (Student, User) tuple for a given student_id, or None."""
    row = (
        db.query(Student, User)
        .join(User, Student.user_id == User.id)
        .filter(Student.id == str(student_id))
        .first()
    )
    return row  # type: ignore[return-value]


def list_students_with_mastery(
    db: Session,
    *,
    offset: int = 0,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Return a list of students with their aggregated learner profile stats.
    Suitable for the teacher's student-list view.
    """
    rows = (
        db.query(Student, User, LearnerProfile)
        .join(User, Student.user_id == User.id)
        .outerjoin(LearnerProfile, LearnerProfile.student_id == Student.id)
        .offset(offset)
        .limit(limit)
        .all()
    )
    results = []
    for student, user, profile in rows:
        mastery_records: list[StudentTopicMastery] = (
            db.query(StudentTopicMastery)
            .filter(StudentTopicMastery.student_id == student.id)
            .all()
        )
        started = [m for m in mastery_records if m.attempts > 0]
        mastered = [m for m in started if m.mastery_level == "mastered"]
        results.append(
            {
                "student_id": str(student.id),
                "full_name": student.full_name,
                "email": user.email,
                "overall_mastery": profile.overall_mastery if profile else 0.0,
                "engagement_score": profile.engagement_score if profile else 0.0,
                "topics_started": len(started),
                "topics_mastered": len(mastered),
                "current_streak_days": profile.current_streak_days if profile else 0,
                "at_risk": (profile.overall_mastery < 0.35 if profile else True)
                or (profile.engagement_score < 0.30 if profile else True),
            }
        )
    return results


def count_students(db: Session) -> int:
    """Return total number of student records."""
    return db.query(Student).count()
