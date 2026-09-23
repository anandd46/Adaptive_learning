"""
Unit tests for the Knowledge Gap Detection engine.
"""
import uuid
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from app.knowledge_gap.engine import detect_knowledge_gaps_for_topic
from app.models.models import KnowledgeGap, Prerequisite, StudentTopicMastery, Topic, Student, User


@pytest.fixture
def student_topic_setup(db_session: Session):
    """Sets up a student, user, and a topic for testing."""
    user = User(email=f"test_{uuid.uuid4()}@test.com", hashed_password="pw", role="student")
    db_session.add(user)
    db_session.flush()

    student = Student(user_id=user.id, full_name="Gap Test Student")
    db_session.add(student)
    db_session.flush()

    topic = Topic(course_id=uuid.uuid4(), title="Test Topic")
    # Course needs to exist or we ignore foreign key (SQLite might ignore by default, but let's be safe)
    # Actually Topic.course_id requires a Course, so let's just create one or use dummy
    # Assuming SQLite foreign keys are OFF or we can insert directly. Let's try.
    db_session.add(topic)
    db_session.flush()

    return student, topic


@patch("app.knowledge_gap.engine.compute_performance_features")
def test_detect_gap_high_severity(mock_features, db_session: Session, student_topic_setup):
    student, topic = student_topic_setup
    
    mock_features.return_value = {
        "accuracy_trend": -0.2,  # Big drop
        "retry_rate": 0.8,       # Lots of retries
        "recent_accuracy": 0.2,
        "average_accuracy": 0.4,
    }

    # Add mastery record with low score
    mastery = StudentTopicMastery(
        student_id=student.id,
        topic_id=topic.id,
        attempts=5,
        mastery_score=0.10,
        confidence=0.5
    )
    db_session.add(mastery)
    db_session.commit()

    gap = detect_knowledge_gaps_for_topic(db_session, student.id, topic.id)
    
    assert gap is not None
    assert gap.gap_score > 0.6  # Should be high or critical
    assert gap.is_active is True
    assert gap.severity in ["high", "critical"]


@patch("app.knowledge_gap.engine.compute_performance_features")
def test_detect_gap_no_gap(mock_features, db_session: Session, student_topic_setup):
    student, topic = student_topic_setup
    
    mock_features.return_value = {
        "accuracy_trend": 0.1,   # Improving
        "retry_rate": 0.05,      # Few retries
        "recent_accuracy": 0.9,
        "average_accuracy": 0.8,
    }

    # Add mastery record with high score
    mastery = StudentTopicMastery(
        student_id=student.id,
        topic_id=topic.id,
        attempts=5,
        mastery_score=0.90,
        confidence=0.8
    )
    db_session.add(mastery)
    db_session.commit()

    gap = detect_knowledge_gaps_for_topic(db_session, student.id, topic.id)
    
    assert gap is None


@patch("app.knowledge_gap.engine.compute_performance_features")
def test_resolve_existing_gap(mock_features, db_session: Session, student_topic_setup):
    student, topic = student_topic_setup
    
    # Setup an existing active gap
    existing_gap = KnowledgeGap(
        student_id=student.id,
        topic_id=topic.id,
        gap_score=0.8,
        severity="high",
        is_active=True
    )
    db_session.add(existing_gap)
    
    # Now the student has improved
    mock_features.return_value = {
        "accuracy_trend": 0.2,
        "retry_rate": 0.1,
    }
    mastery = StudentTopicMastery(
        student_id=student.id,
        topic_id=topic.id,
        attempts=10,
        mastery_score=0.85,
        confidence=0.9
    )
    db_session.add(mastery)
    db_session.commit()

    # Run detection
    result = detect_knowledge_gaps_for_topic(db_session, student.id, topic.id)
    
    # Gap should be resolved (function returns None for no active gap)
    assert result is None
    
    # Verify in DB
    db_gap = db_session.query(KnowledgeGap).filter_by(id=existing_gap.id).first()
    assert db_gap.is_active is False
    assert db_gap.resolved_at is not None
