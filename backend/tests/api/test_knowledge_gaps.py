"""
API tests for Knowledge Gaps.
"""
import uuid
import pytest
from fastapi.testclient import TestClient

from app.models.models import KnowledgeGap, Topic


@pytest.fixture
def test_topic(db_session):
    topic = Topic(course_id=uuid.uuid4(), title="Test Topic for Gap")
    db_session.add(topic)
    db_session.commit()
    return topic


@pytest.fixture
def active_gap(client, db_session, registered_student, student_auth_headers, test_topic):
    resp = client.get("/api/v1/students/me", headers=student_auth_headers)
    student_id = resp.json()["data"]["student_id"]
    gap = KnowledgeGap(
        student_id=uuid.UUID(student_id),
        topic_id=test_topic.id,
        gap_score=0.85,
        severity="critical",
        priority=1,
        is_active=True,
        confidence=0.9
    )
    db_session.add(gap)
    db_session.commit()
    return gap


def test_student_get_knowledge_gaps(client: TestClient, student_auth_headers, active_gap):
    """Test that a student can get their own knowledge gaps."""
    response = client.get("/api/v1/students/me/knowledge-gaps", headers=student_auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["gap_score"] == 0.85
    assert data[0]["severity"] == "critical"


def test_student_resolve_knowledge_gap(client: TestClient, student_auth_headers, active_gap, db_session):
    """Test that a student can resolve their knowledge gap."""
    response = client.post(f"/api/v1/students/me/knowledge-gaps/{active_gap.id}/resolve", headers=student_auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["is_active"] is False
    assert data["resolved_at"] is not None
    
    # Verify in DB
    db_gap = db_session.query(KnowledgeGap).filter_by(id=active_gap.id).first()
    assert db_gap.is_active is False


def test_teacher_get_student_knowledge_gaps(client: TestClient, teacher_auth_headers, student_auth_headers, active_gap, registered_student):
    """Test that a teacher can view a student's knowledge gaps."""
    resp = client.get("/api/v1/students/me", headers=student_auth_headers)
    student_id = resp.json()["data"]["student_id"]
    response = client.get(f"/api/v1/teacher/students/{student_id}/knowledge-gaps", headers=teacher_auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["gap_score"] == 0.85


def test_teacher_cannot_get_knowledge_gaps_with_student_token(client: TestClient, student_auth_headers, active_gap, registered_student):
    """Test that a student cannot hit the teacher endpoint."""
    resp = client.get("/api/v1/students/me", headers=student_auth_headers)
    student_id = resp.json()["data"]["student_id"]
    response = client.get(f"/api/v1/teacher/students/{student_id}/knowledge-gaps", headers=student_auth_headers)
    assert response.status_code == 403
