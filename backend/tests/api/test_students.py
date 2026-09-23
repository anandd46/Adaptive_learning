"""
API tests for student endpoints (Phase 2).

Tests:
- GET /api/v1/students/me               — current student profile
- GET /api/v1/students/me/mastery       — mastery records list
- GET /api/v1/students/me/mastery/{id}  — single topic mastery (404 case)
- GET /api/v1/students/me/profile       — learner profile
- POST /api/v1/students/me/profile/refresh — analytics refresh
- GET /api/v1/students/me/performance   — performance summary
"""
import pytest
from fastapi.testclient import TestClient


class TestStudentMe:
    """Tests for GET /api/v1/students/me."""

    def test_get_my_profile_success(self, client: TestClient, student_auth_headers: dict):
        """Authenticated student gets their profile."""
        resp = client.get("/api/v1/students/me", headers=student_auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert "student_id" in data
        assert "full_name" in data
        assert "email" in data
        assert "enrolled_at" in data

    def test_teacher_cannot_access_student_me(self, client: TestClient, teacher_auth_headers: dict):
        """Teacher role cannot access student-only endpoint."""
        resp = client.get("/api/v1/students/me", headers=teacher_auth_headers)
        assert resp.status_code in (401, 403)

    def test_unauthenticated_gets_401(self, client: TestClient):
        resp = client.get("/api/v1/students/me")
        assert resp.status_code in (401, 403)


class TestStudentMastery:
    """Tests for GET /api/v1/students/me/mastery."""

    def test_mastery_list_empty_for_new_student(
        self, client: TestClient, student_auth_headers: dict
    ):
        """New student has no mastery records — returns empty list."""
        resp = client.get("/api/v1/students/me/mastery", headers=student_auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert isinstance(body["data"], list)
        assert body["total"] == 0

    def test_mastery_response_has_pagination(
        self, client: TestClient, student_auth_headers: dict
    ):
        """Response always includes pagination metadata."""
        resp = client.get("/api/v1/students/me/mastery", headers=student_auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "page" in body
        assert "page_size" in body
        assert "total_pages" in body

    def test_mastery_unauthenticated_blocked(self, client: TestClient):
        resp = client.get("/api/v1/students/me/mastery")
        assert resp.status_code in (401, 403)

    def test_single_topic_mastery_not_found(
        self, client: TestClient, student_auth_headers: dict
    ):
        """Requesting mastery for a topic with no record returns 404."""
        import uuid
        resp = client.get(
            f"/api/v1/students/me/mastery/{uuid.uuid4()}",
            headers=student_auth_headers,
        )
        assert resp.status_code == 404


class TestLearnerProfile:
    """Tests for GET /api/v1/students/me/profile."""

    def test_get_profile_returns_structure(
        self, client: TestClient, student_auth_headers: dict
    ):
        """Profile is returned (or created) with expected fields."""
        resp = client.get("/api/v1/students/me/profile", headers=student_auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert "student_id" in data
        assert "overall_mastery" in data
        assert "engagement_score" in data
        assert "weak_topics" in data
        assert "strong_topics" in data
        assert isinstance(data["weak_topics"], list)
        assert isinstance(data["strong_topics"], list)
        assert 0.0 <= data["overall_mastery"] <= 1.0

    def test_get_profile_unauthenticated(self, client: TestClient):
        resp = client.get("/api/v1/students/me/profile")
        assert resp.status_code in (401, 403)

    def test_teacher_cannot_access_own_profile(
        self, client: TestClient, teacher_auth_headers: dict
    ):
        resp = client.get("/api/v1/students/me/profile", headers=teacher_auth_headers)
        assert resp.status_code in (401, 403)


class TestProfileRefresh:
    """Tests for POST /api/v1/students/me/profile/refresh."""

    def test_refresh_profile_success(
        self, client: TestClient, student_auth_headers: dict
    ):
        """Profile refresh returns updated profile with correct structure."""
        resp = client.post(
            "/api/v1/students/me/profile/refresh",
            headers=student_auth_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        assert "overall_mastery" in body["data"]
        assert body["message"] is not None

    def test_refresh_profile_unauthenticated(self, client: TestClient):
        resp = client.post("/api/v1/students/me/profile/refresh")
        assert resp.status_code in (401, 403)


class TestPerformanceSummary:
    """Tests for GET /api/v1/students/me/performance."""

    def test_performance_summary_structure(
        self, client: TestClient, student_auth_headers: dict
    ):
        """Performance summary has all required fields for a new student."""
        resp = client.get(
            "/api/v1/students/me/performance", headers=student_auth_headers
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert "overall_mastery" in data
        assert "topics_started" in data
        assert "topics_mastered" in data
        assert "total_quiz_attempts" in data
        assert "average_accuracy_across_topics" in data
        assert "engagement_score" in data
        assert "current_streak_days" in data
        # New student has zero interactions
        assert data["topics_started"] == 0
        assert data["total_quiz_attempts"] == 0

    def test_performance_unauthenticated(self, client: TestClient):
        resp = client.get("/api/v1/students/me/performance")
        assert resp.status_code in (401, 403)
