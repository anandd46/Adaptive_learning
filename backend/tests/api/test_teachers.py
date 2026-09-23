"""
API tests for teacher endpoints (Phase 2).

Tests:
- GET /api/v1/teacher/dashboard        — class statistics (teacher-only)
- GET /api/v1/teacher/students         — paginated student list
- GET /api/v1/teacher/students/{id}    — individual student profile
"""
import pytest
from fastapi.testclient import TestClient


class TestTeacherDashboard:
    """Tests for GET /api/v1/teacher/dashboard."""

    def test_dashboard_success_for_teacher(
        self, client: TestClient, teacher_auth_headers: dict
    ):
        """Teacher gets class dashboard with expected structure."""
        resp = client.get("/api/v1/teacher/dashboard", headers=teacher_auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert "total_students" in data
        assert "active_students_7d" in data
        assert "average_class_mastery" in data
        assert "at_risk_count" in data
        assert "topics_with_most_gaps" in data
        assert "class_accuracy_by_topic" in data
        assert isinstance(data["topics_with_most_gaps"], list)
        assert isinstance(data["class_accuracy_by_topic"], list)

    def test_dashboard_mastery_values_in_range(
        self, client: TestClient, teacher_auth_headers: dict
    ):
        """Average class mastery must be between 0 and 1."""
        resp = client.get("/api/v1/teacher/dashboard", headers=teacher_auth_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert 0.0 <= data["average_class_mastery"] <= 1.0
        assert data["at_risk_count"] >= 0
        assert data["total_students"] >= 0

    def test_student_cannot_access_dashboard(
        self, client: TestClient, student_auth_headers: dict
    ):
        """Students must not access teacher dashboard."""
        resp = client.get("/api/v1/teacher/dashboard", headers=student_auth_headers)
        assert resp.status_code in (401, 403)

    def test_unauthenticated_dashboard_blocked(self, client: TestClient):
        resp = client.get("/api/v1/teacher/dashboard")
        assert resp.status_code in (401, 403)


class TestTeacherStudentList:
    """Tests for GET /api/v1/teacher/students."""

    def test_student_list_success(
        self, client: TestClient, teacher_auth_headers: dict
    ):
        """Teacher can fetch paginated student list."""
        resp = client.get("/api/v1/teacher/students", headers=teacher_auth_headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        assert isinstance(body["data"], list)
        assert "total" in body
        assert "page" in body
        assert "page_size" in body

    def test_student_list_contains_registered_student(
        self,
        client: TestClient,
        teacher_auth_headers: dict,
        registered_student: dict,
    ):
        """After a student registers, they appear in the teacher's list."""
        resp = client.get("/api/v1/teacher/students", headers=teacher_auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1

    def test_student_list_entry_has_expected_fields(
        self,
        client: TestClient,
        teacher_auth_headers: dict,
        registered_student: dict,
    ):
        """Each entry in the student list has the required summary fields."""
        resp = client.get("/api/v1/teacher/students", headers=teacher_auth_headers)
        assert resp.status_code == 200
        entries = resp.json()["data"]
        if entries:
            entry = entries[0]
            assert "student_id" in entry
            assert "full_name" in entry
            assert "email" in entry
            assert "overall_mastery" in entry
            assert "engagement_score" in entry
            assert "topics_started" in entry
            assert "topics_mastered" in entry
            assert "at_risk" in entry

    def test_student_cannot_list_students(
        self, client: TestClient, student_auth_headers: dict
    ):
        resp = client.get("/api/v1/teacher/students", headers=student_auth_headers)
        assert resp.status_code in (401, 403)

    def test_pagination_params_respected(
        self, client: TestClient, teacher_auth_headers: dict
    ):
        """Page size parameter is applied."""
        resp = client.get(
            "/api/v1/teacher/students?page=1&page_size=1",
            headers=teacher_auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["page_size"] == 1
        assert len(body["data"]) <= 1


class TestTeacherStudentProfile:
    """Tests for GET /api/v1/teacher/students/{student_id}."""

    def test_get_student_profile_success(
        self,
        client: TestClient,
        teacher_auth_headers: dict,
        registered_student: dict,
    ):
        """Teacher can view an individual student's learner profile."""
        # First get the student id from the list
        list_resp = client.get("/api/v1/teacher/students", headers=teacher_auth_headers)
        students = list_resp.json()["data"]
        if not students:
            pytest.skip("No students in DB")

        student_id = students[0]["student_id"]
        resp = client.get(
            f"/api/v1/teacher/students/{student_id}",
            headers=teacher_auth_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert "student_id" in data
        assert "overall_mastery" in data
        assert "weak_topics" in data

    def test_get_nonexistent_student_returns_404(
        self, client: TestClient, teacher_auth_headers: dict
    ):
        import uuid
        resp = client.get(
            f"/api/v1/teacher/students/{uuid.uuid4()}",
            headers=teacher_auth_headers,
        )
        assert resp.status_code == 404

    def test_student_cannot_view_other_profiles(
        self,
        client: TestClient,
        student_auth_headers: dict,
    ):
        import uuid
        resp = client.get(
            f"/api/v1/teacher/students/{uuid.uuid4()}",
            headers=student_auth_headers,
        )
        assert resp.status_code in (401, 403)
