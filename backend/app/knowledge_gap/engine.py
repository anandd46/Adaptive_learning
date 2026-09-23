"""
Knowledge Gap Detection Engine — Phase 3.
Computes multi-signal knowledge gaps based on mastery, performance features, and prerequisites.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.analytics.engine import compute_performance_features
from app.models.models import KnowledgeGap, Prerequisite, StudentTopicMastery
from app.repositories.knowledge_gap_repository import (
    resolve_knowledge_gap,
    upsert_knowledge_gap,
)

logger = logging.getLogger(__name__)


def _to_uuid(val: str | uuid.UUID) -> uuid.UUID:
    """Coerce str or UUID to uuid.UUID for SQLAlchemy queries."""
    if isinstance(val, uuid.UUID):
        return val
    return uuid.UUID(str(val))


def detect_knowledge_gaps_for_topic(
    db: Session,
    student_id: str | uuid.UUID,
    topic_id: str | uuid.UUID,
) -> KnowledgeGap | None:
    """
    Detect knowledge gaps for a specific topic using multiple signals.
    Updates the database with the findings (creates/updates a KnowledgeGap, or resolves an existing one).
    Returns the KnowledgeGap if one is active, otherwise None.
    """
    student_uuid = _to_uuid(student_id)
    topic_uuid = _to_uuid(topic_id)

    mastery = (
        db.query(StudentTopicMastery)
        .filter(
            StudentTopicMastery.student_id == student_uuid,
            StudentTopicMastery.topic_id == topic_uuid,
        )
        .first()
    )

    if not mastery or mastery.attempts == 0:
        return None

    features = compute_performance_features(db, str(student_uuid), str(topic_uuid))

    # Signal 1: Mastery Deficit (Target mastery is 0.70)
    target_mastery = 0.70
    mastery_deficit = max(0.0, target_mastery - mastery.mastery_score) / target_mastery

    # Signal 2: Accuracy Trend (Negative trend)
    trend = features.get("accuracy_trend", 0.0)
    accuracy_deficit = 0.0
    if trend < -0.05:  # Noticeable drop in accuracy
        accuracy_deficit = min(1.0, abs(trend) * 2)

    # Signal 3: Retry Rate (High retries indicates struggle)
    retry_rate = features.get("retry_rate", 0.0)
    retry_penalty = min(1.0, retry_rate * 1.5)  # E.g., 0.5 retry rate -> 0.75 penalty

    # Signal 4: Prerequisite Gaps
    prereqs = (
        db.query(Prerequisite)
        .filter(Prerequisite.topic_id == topic_uuid)
        .all()
    )
    prereq_penalty = 0.0
    prereq_info: dict[str, Any] = {}

    for p in prereqs:
        p_mastery = (
            db.query(StudentTopicMastery)
            .filter(
                StudentTopicMastery.student_id == student_uuid,
                StudentTopicMastery.topic_id == p.prerequisite_topic_id,
            )
            .first()
        )
        score = p_mastery.mastery_score if p_mastery else 0.0
        if score < p.required_mastery:
            deficit = (p.required_mastery - score) / p.required_mastery
            prereq_penalty += deficit
            prereq_info[str(p.prerequisite_topic_id)] = {
                "required": p.required_mastery,
                "actual": score,
            }

    if prereqs:
        prereq_penalty = min(1.0, prereq_penalty / len(prereqs))

    # Compute final Gap Score
    gap_score = (
        0.4 * mastery_deficit
        + 0.2 * accuracy_deficit
        + 0.2 * retry_penalty
        + 0.2 * prereq_penalty
    )
    gap_score = round(min(1.0, gap_score), 4)

    # Check for existing active gap
    existing_gap = (
        db.query(KnowledgeGap)
        .filter(
            KnowledgeGap.student_id == student_uuid,
            KnowledgeGap.topic_id == topic_uuid,
            KnowledgeGap.is_active == True,
        )
        .first()
    )

    threshold = 0.40  # Minimum gap score to flag as a Knowledge Gap

    if gap_score >= threshold:
        # Map gap score to severity
        severity = "low"
        priority = 4
        if gap_score > 0.8:
            severity = "critical"
            priority = 1
        elif gap_score > 0.6:
            severity = "high"
            priority = 2
        elif gap_score > 0.5:
            severity = "medium"
            priority = 3

        evidence = {
            "mastery_deficit": round(mastery_deficit, 4),
            "accuracy_deficit": round(accuracy_deficit, 4),
            "retry_penalty": round(retry_penalty, 4),
            "prereq_penalty": round(prereq_penalty, 4),
            "retry_rate": retry_rate,
            "accuracy_trend": trend,
            "mastery_score": mastery.mastery_score,
        }

        gap = upsert_knowledge_gap(
            db=db,
            student_id=student_uuid,
            topic_id=topic_uuid,
            gap_score=gap_score,
            severity=severity,
            priority=priority,
            evidence=evidence,
            confidence=mastery.confidence,
            prerequisite_info=prereq_info,
        )
        return gap
    elif existing_gap:
        # Gap has fallen below threshold, mark as resolved
        resolve_knowledge_gap(db, existing_gap)
        return None

    return None


def detect_all_knowledge_gaps(db: Session, student_id: str | uuid.UUID) -> None:
    """
    Run the knowledge gap detection for all topics the student has started.
    """
    student_uuid = _to_uuid(student_id)
    mastery_records = (
        db.query(StudentTopicMastery.topic_id)
        .filter(
            StudentTopicMastery.student_id == student_uuid,
            StudentTopicMastery.attempts > 0,
        )
        .all()
    )

    for (topic_id,) in mastery_records:
        detect_knowledge_gaps_for_topic(db, student_uuid, topic_id)
