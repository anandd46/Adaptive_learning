"""
Knowledge Gap repository — data access layer for knowledge gap operations.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.models import KnowledgeGap, Topic


def _to_uuid(val: str | uuid.UUID) -> uuid.UUID:
    """Coerce str or UUID to uuid.UUID for SQLAlchemy queries."""
    if isinstance(val, uuid.UUID):
        return val
    return uuid.UUID(str(val))


def get_active_gaps_for_student(
    db: Session,
    student_id: str | uuid.UUID,
) -> list[dict[str, Any]]:
    """
    Return all active knowledge gaps for a student, ordered by priority (highest first)
    then severity. Enriches with topic_title.
    """
    gaps = (
        db.query(KnowledgeGap, Topic)
        .join(Topic, KnowledgeGap.topic_id == Topic.id)
        .filter(
            KnowledgeGap.student_id == _to_uuid(student_id),
            KnowledgeGap.is_active == True,
        )
        .order_by(KnowledgeGap.priority.asc(), KnowledgeGap.gap_score.desc())
        .all()
    )
    
    return [
        {
            "id": gap.id,
            "student_id": gap.student_id,
            "topic_id": gap.topic_id,
            "topic_title": topic.title,
            "gap_score": gap.gap_score,
            "severity": gap.severity,
            "priority": gap.priority,
            "evidence": gap.evidence,
            "confidence": gap.confidence,
            "affected_concepts": gap.affected_concepts,
            "prerequisite_info": gap.prerequisite_info,
            "is_active": gap.is_active,
            "detected_at": gap.detected_at,
            "resolved_at": gap.resolved_at,
        }
        for gap, topic in gaps
    ]


def upsert_knowledge_gap(
    db: Session,
    student_id: str | uuid.UUID,
    topic_id: str | uuid.UUID,
    gap_score: float,
    severity: str,
    priority: int,
    evidence: dict[str, Any],
    confidence: float,
    affected_concepts: list[Any] | None = None,
    prerequisite_info: dict[str, Any] | None = None,
) -> KnowledgeGap:
    """
    Create a new knowledge gap or update an existing one if the student still has a gap in the topic.
    If the gap was previously resolved but is detected again, it is marked active again.
    """
    gap = (
        db.query(KnowledgeGap)
        .filter(
            KnowledgeGap.student_id == _to_uuid(student_id),
            KnowledgeGap.topic_id == _to_uuid(topic_id),
        )
        .first()
    )

    if not gap:
        gap = KnowledgeGap(
            student_id=_to_uuid(student_id),
            topic_id=_to_uuid(topic_id),
        )
        db.add(gap)

    gap.gap_score = gap_score
    gap.severity = severity
    gap.priority = priority
    gap.evidence = evidence
    gap.confidence = confidence
    gap.affected_concepts = affected_concepts or []
    gap.prerequisite_info = prerequisite_info or {}
    gap.is_active = True
    gap.resolved_at = None
    gap.detected_at = datetime.now(tz=timezone.utc)
    
    db.flush()
    return gap


def get_gap_by_id(db: Session, gap_id: str | uuid.UUID) -> KnowledgeGap | None:
    """Fetch a knowledge gap by its ID."""
    return (
        db.query(KnowledgeGap)
        .filter(KnowledgeGap.id == _to_uuid(gap_id))
        .first()
    )


def resolve_knowledge_gap(
    db: Session,
    gap: KnowledgeGap,
) -> KnowledgeGap:
    """Mark a knowledge gap as resolved."""
    gap.is_active = False
    gap.resolved_at = datetime.now(tz=timezone.utc)
    db.flush()
    return gap
