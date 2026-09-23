"""
Learning Analytics Engine — Phase 2.

Computes behavioral and performance features from raw interaction data
stored in the database. All functions operate on SQLAlchemy ORM objects
and write back to the DB where indicated.

IMPORTANT: All computed values are descriptive statistics derived from
student interaction data. They are NOT research-validated metrics,
ML model outputs, or calibrated predictions.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.analytics.mastery import (
    classify_mastery_level,
    compute_mastery_confidence,
    compute_mastery_score,
)
from app.models.models import (
    LearnerProfile,
    LearningSession,
    QuizAttempt,
    StudentAnswer,
    StudentEvent,
    StudentTopicMastery,
    Topic,
)

logger = logging.getLogger(__name__)

# ─── Recent-window size for accuracy calculations ─────────────────────────────
RECENT_ATTEMPTS_WINDOW = 3


def _to_uuid(val: str | uuid.UUID) -> uuid.UUID:
    """Coerce str or UUID to uuid.UUID for SQLAlchemy queries."""
    if isinstance(val, uuid.UUID):
        return val
    return uuid.UUID(str(val))


# ─── Performance Feature Engineering ─────────────────────────────────────────

def compute_performance_features(
    db: Session,
    student_id: str,
    topic_id: str,
) -> dict[str, Any]:
    """
    Compute per-topic behavioral and performance features for a student.

    Features derived from QuizAttempt + StudentAnswer records:
    - recent_accuracy       — accuracy in last 3 completed attempts
    - average_accuracy      — historical average accuracy
    - accuracy_trend        — recent_accuracy minus average_accuracy
    - avg_time_per_question — average seconds per answer
    - retry_rate            — fraction of answers with attempt_number > 1
    - hint_usage_rate       — fraction of answers where hint_used = True
    - attempt_count         — total completed quiz attempts for this topic
    - total_questions_answered — total StudentAnswer rows

    Returns an empty-feature dict if the student has no attempts.
    """
    # Fetch all completed quiz attempts for this student-topic pair
    attempts: list[QuizAttempt] = (
        db.query(QuizAttempt)
        .join(QuizAttempt.quiz)
        .filter(
            QuizAttempt.student_id == _to_uuid(student_id),
            QuizAttempt.quiz.has(topic_id=_to_uuid(topic_id)),  # type: ignore[union-attr]
            QuizAttempt.status == "completed",
        )
        .order_by(QuizAttempt.completed_at)
        .all()
    )

    attempt_count = len(attempts)

    if attempt_count == 0:
        return _empty_performance_features()

    # Per-attempt accuracy
    attempt_accuracies = [
        (a.correct_count / a.total_questions) if a.total_questions > 0 else 0.0
        for a in attempts
    ]
    average_accuracy = sum(attempt_accuracies) / len(attempt_accuracies)

    # Recent accuracy (last RECENT_ATTEMPTS_WINDOW)
    recent_attempts = attempts[-RECENT_ATTEMPTS_WINDOW:]
    recent_accuracies = [
        (a.correct_count / a.total_questions) if a.total_questions > 0 else 0.0
        for a in recent_attempts
    ]
    recent_accuracy = sum(recent_accuracies) / len(recent_accuracies)

    accuracy_trend = round(recent_accuracy - average_accuracy, 4)

    # Gather all answers
    attempt_ids = [a.id for a in attempts]
    answers: list[StudentAnswer] = (
        db.query(StudentAnswer)
        .filter(StudentAnswer.attempt_id.in_(attempt_ids))
        .all()
    )
    total_questions_answered = len(answers)

    # Time per question
    time_values = [a.time_spent_seconds for a in answers if a.time_spent_seconds > 0]
    avg_time = (sum(time_values) / len(time_values)) if time_values else 0.0

    # Retry rate
    retried = sum(1 for a in answers if a.attempt_number > 1)
    retry_rate = round(retried / total_questions_answered, 4) if total_questions_answered > 0 else 0.0

    # Hint usage rate
    hinted = sum(1 for a in answers if a.hint_used)
    hint_usage_rate = round(hinted / total_questions_answered, 4) if total_questions_answered > 0 else 0.0

    return {
        "recent_accuracy": round(recent_accuracy, 4),
        "average_accuracy": round(average_accuracy, 4),
        "accuracy_trend": accuracy_trend,
        "avg_time_per_question_seconds": round(avg_time, 2),
        "retry_rate": retry_rate,
        "hint_usage_rate": hint_usage_rate,
        "attempt_count": attempt_count,
        "total_questions_answered": total_questions_answered,
    }


def _empty_performance_features() -> dict[str, Any]:
    return {
        "recent_accuracy": 0.0,
        "average_accuracy": 0.0,
        "accuracy_trend": 0.0,
        "avg_time_per_question_seconds": 0.0,
        "retry_rate": 0.0,
        "hint_usage_rate": 0.0,
        "attempt_count": 0,
        "total_questions_answered": 0,
    }


# ─── Engagement Score ─────────────────────────────────────────────────────────

def compute_engagement_score(
    db: Session,
    student_id: str,
    *,
    lookback_days: int = 30,
) -> float:
    """
    Compute an engagement score (0.0–1.0) for a student based on recent
    session activity.

    Factors:
    - Sessions in last 30 days (normalized to ~5/week target)
    - Average session duration (normalized to 20-minute target)
    - Session consistency (number of distinct active days / lookback_days)

    NOTE: This is a simple heuristic score. It is NOT a validated
    engagement metric from the educational research literature.

    Returns:
        Engagement score in [0.0, 1.0].
    """
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=lookback_days)

    sessions: list[LearningSession] = (
        db.query(LearningSession)
        .filter(
            LearningSession.student_id == _to_uuid(student_id),
            LearningSession.started_at >= cutoff,
        )
        .all()
    )

    if not sessions:
        return 0.0

    session_count = len(sessions)
    target_sessions = (lookback_days / 7) * 5  # 5 sessions/week target
    session_factor = min(1.0, session_count / max(1, target_sessions))

    # Average duration
    durations = [s.duration_seconds for s in sessions if s.duration_seconds > 0]
    avg_duration = (sum(durations) / len(durations)) if durations else 0.0
    target_duration = 20 * 60  # 20 minutes in seconds
    duration_factor = min(1.0, avg_duration / max(1, target_duration))

    # Consistency: fraction of days with at least one session
    active_days = len({s.started_at.date() for s in sessions if s.started_at})
    consistency_factor = min(1.0, active_days / max(1, lookback_days))

    score = 0.50 * session_factor + 0.30 * duration_factor + 0.20 * consistency_factor
    return round(max(0.0, min(1.0, score)), 4)


# ─── Mastery Update (DB write) ────────────────────────────────────────────────

def update_student_topic_mastery(
    db: Session,
    student_id: str,
    topic_id: str,
) -> StudentTopicMastery:
    """
    Recompute and persist the StudentTopicMastery record for a student-topic pair.

    Steps:
    1. Fetch performance features from quiz/answer data
    2. Compute mastery score and confidence
    3. Classify mastery level
    4. Upsert the StudentTopicMastery row

    Returns the updated StudentTopicMastery ORM object.
    """
    features = compute_performance_features(db, student_id, topic_id)

    mastery_score = compute_mastery_score(
        attempts=features["attempt_count"],
        correct_count=features["total_questions_answered"],  # proxy for answered count
        recent_accuracy=features["recent_accuracy"],
        average_accuracy=features["average_accuracy"],
    )
    confidence = compute_mastery_confidence(features["attempt_count"])
    level = classify_mastery_level(mastery_score)

    record: StudentTopicMastery | None = (
        db.query(StudentTopicMastery)
        .filter(
            StudentTopicMastery.student_id == _to_uuid(student_id),
            StudentTopicMastery.topic_id == _to_uuid(topic_id),
        )
        .first()
    )

    now = datetime.now(tz=timezone.utc)

    if record is None:
        record = StudentTopicMastery(
            student_id=_to_uuid(student_id),
            topic_id=_to_uuid(topic_id),
        )
        db.add(record)

    record.mastery_score = mastery_score
    record.confidence = confidence
    record.mastery_level = level
    record.recent_accuracy = features["recent_accuracy"]
    record.average_accuracy = features["average_accuracy"]
    record.attempts = features["attempt_count"]
    record.last_assessed_at = now

    db.flush()
    logger.debug(
        "Updated mastery record",
        extra={
            "student_id": str(student_id),
            "topic_id": str(topic_id),
            "score": mastery_score,
            "level": level,
        },
    )
    return record


# ─── Learner Profile Update (DB write) ───────────────────────────────────────

def update_learner_profile(
    db: Session,
    student_id: str,
) -> LearnerProfile:
    """
    Recompute and persist the LearnerProfile for a student.

    The profile aggregates:
    - overall_mastery         — average mastery score across started topics
    - engagement_score        — computed by compute_engagement_score()
    - weak_topics             — topic_ids where mastery < 0.35
    - strong_topics           — topic_ids where mastery >= 0.85
    - performance_summary     — {topic_id: {"score": ..., "level": ...}}
    - engagement_metrics      — {session_count_30d, avg_session_seconds_30d, active_days_30d}
    - current_streak_days     — consecutive days with at least one event up to today

    Returns the updated LearnerProfile ORM object.
    """
    # Fetch all mastery records
    mastery_records: list[StudentTopicMastery] = (
        db.query(StudentTopicMastery)
        .filter(StudentTopicMastery.student_id == _to_uuid(student_id))
        .all()
    )

    started = [m for m in mastery_records if m.attempts > 0]
    overall_mastery = (
        sum(m.mastery_score for m in started) / len(started) if started else 0.0
    )
    overall_mastery = round(overall_mastery, 4)

    weak_topics = [str(m.topic_id) for m in started if m.mastery_score < 0.35]
    strong_topics = [str(m.topic_id) for m in started if m.mastery_score >= 0.85]

    performance_summary = {
        str(m.topic_id): {
            "score": m.mastery_score,
            "level": m.mastery_level,
            "accuracy": m.average_accuracy,
        }
        for m in mastery_records
    }

    engagement_score = compute_engagement_score(db, student_id)

    # Session engagement metrics
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=30)
    sessions_30d: list[LearningSession] = (
        db.query(LearningSession)
        .filter(
            LearningSession.student_id == _to_uuid(student_id),
            LearningSession.started_at >= cutoff,
        )
        .all()
    )
    avg_session = (
        sum(s.duration_seconds for s in sessions_30d) / len(sessions_30d)
        if sessions_30d
        else 0.0
    )
    active_days_30d = len({s.started_at.date() for s in sessions_30d if s.started_at})

    engagement_metrics = {
        "session_count_30d": len(sessions_30d),
        "avg_session_seconds_30d": round(avg_session, 0),
        "active_days_30d": active_days_30d,
    }

    # Streak calculation
    streak = _compute_streak(db, student_id)

    # Upsert profile
    profile: LearnerProfile | None = (
        db.query(LearnerProfile)
        .filter(LearnerProfile.student_id == _to_uuid(student_id))
        .first()
    )
    if profile is None:
        profile = LearnerProfile(student_id=_to_uuid(student_id))
        db.add(profile)

    profile.overall_mastery = overall_mastery
    profile.engagement_score = engagement_score
    profile.weak_topics = weak_topics
    profile.strong_topics = strong_topics
    profile.performance_summary = performance_summary
    profile.engagement_metrics = engagement_metrics
    profile.current_streak_days = streak

    db.flush()
    logger.info(
        "Updated learner profile",
        extra={
            "student_id": str(student_id),
            "overall_mastery": overall_mastery,
            "engagement_score": engagement_score,
            "streak_days": streak,
        },
    )
    return profile


# ─── Streak Calculation ───────────────────────────────────────────────────────

def _compute_streak(db: Session, student_id: str) -> int:
    """
    Count the number of consecutive calendar days (up to and including today)
    on which the student had at least one recorded event.
    """
    today = datetime.now(tz=timezone.utc).date()

    # Get distinct event dates in descending order
    event_dates_q = (
        db.query(func.date(StudentEvent.occurred_at).label("event_date"))
        .filter(StudentEvent.student_id == _to_uuid(student_id))
        .distinct()
        .order_by(func.date(StudentEvent.occurred_at).desc())
        .all()
    )

    if not event_dates_q:
        return 0

    dates = sorted(
        {row.event_date for row in event_dates_q if row.event_date is not None},
        reverse=True,
    )

    if not dates:
        return 0

    # Streak starts only if student was active today or yesterday
    if (today - dates[0]).days > 1:
        return 0

    streak = 0
    expected = dates[0]
    for d in dates:
        if (expected - d).days == 0:
            streak += 1
            expected -= timedelta(days=1)
        elif (expected - d).days > 1:
            break
    return streak


# ─── Class-level Analytics (for Teacher Dashboard) ───────────────────────────

def compute_class_statistics(
    db: Session,
    student_ids: list[str],
) -> dict[str, Any]:
    """
    Compute aggregate class-level analytics for a list of student IDs.

    Returns:
    - average_class_mastery       — mean overall mastery across students
    - at_risk_count               — students with overall_mastery < 0.35
    - topics_with_most_gaps       — top topics by weak-student count
    - class_accuracy_by_topic     — average accuracy per topic across class
    """
    if not student_ids:
        return {
            "average_class_mastery": 0.0,
            "at_risk_count": 0,
            "topics_with_most_gaps": [],
            "class_accuracy_by_topic": [],
        }

    profiles: list[LearnerProfile] = (
        db.query(LearnerProfile)
        .filter(LearnerProfile.student_id.in_([_to_uuid(sid) for sid in student_ids]))
        .all()
    )

    overall_masteries = [p.overall_mastery for p in profiles]
    avg_mastery = (
        sum(overall_masteries) / len(overall_masteries) if overall_masteries else 0.0
    )
    at_risk = sum(1 for m in overall_masteries if m < 0.35)

    # Topic-level class accuracy
    mastery_records: list[StudentTopicMastery] = (
        db.query(StudentTopicMastery)
        .filter(StudentTopicMastery.student_id.in_([_to_uuid(sid) for sid in student_ids]))
        .all()
    )

    topic_stats: dict[str, list[float]] = {}
    for rec in mastery_records:
        tid = str(rec.topic_id)
        topic_stats.setdefault(tid, []).append(rec.average_accuracy)

    # Get topic titles
    topic_ids = list(topic_stats.keys())
    topics: list[Topic] = (
        db.query(Topic).filter(Topic.id.in_(topic_ids)).all()
    ) if topic_ids else []
    topic_title_map = {str(t.id): t.title for t in topics}

    class_accuracy_by_topic = [
        {
            "topic_id": tid,
            "title": topic_title_map.get(tid, "Unknown"),
            "avg_accuracy": round(sum(accs) / len(accs), 4),
            "student_count": len(accs),
        }
        for tid, accs in topic_stats.items()
    ]
    class_accuracy_by_topic.sort(key=lambda x: x["avg_accuracy"])

    # Topics with most struggling students
    weak_topic_counts: dict[str, int] = {}
    for rec in mastery_records:
        if rec.mastery_score < 0.35:
            tid = str(rec.topic_id)
            weak_topic_counts[tid] = weak_topic_counts.get(tid, 0) + 1

    topics_with_most_gaps = [
        {
            "topic_id": tid,
            "title": topic_title_map.get(tid, "Unknown"),
            "weak_student_count": cnt,
        }
        for tid, cnt in sorted(weak_topic_counts.items(), key=lambda x: -x[1])
    ][:10]

    return {
        "average_class_mastery": round(avg_mastery, 4),
        "at_risk_count": at_risk,
        "topics_with_most_gaps": topics_with_most_gaps,
        "class_accuracy_by_topic": class_accuracy_by_topic,
    }
