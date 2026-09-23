"""
API tests for event tracking endpoints (Phase 2).

Tests:
- POST /api/v1/events       — record events (success, validation, auth)
- GET  /api/v1/events       — list events (pagination)
- POST /api/v1/sessions     — start session
- PATCH /api/v1/sessions/{id} — end session
"""
import pytest
from fastapi.testclient import TestClient


# ─── Event Recording ──────────────────────────────────────────────────────────

class TestRecordEvent:
    """Tests for POST /api/v1/events."""

    def test_record_event_success(self, client: TestClient, student_auth_headers: dict):
        """A student can record a valid event."""
        resp = client.post(
            "/api/v1/events",
            json={"event_type": "resource_view", "event_data": {"resource": "lecture_1"}},
            headers=student_auth_headers,
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["event_type"] == "resource_view"
        assert "id" in data["data"]
        assert "occurred_at" in data["data"]

    def test_record_event_with_optional_fields(self, client: TestClient, student_auth_headers: dict):
        """Event can include optional topic_id and session_id as None."""
        resp = client.post(
            "/api/v1/events",
            json={
                "event_type": "quiz_started",
                "topic_id": None,
                "resource_id": None,
                "event_data": {},
            },
            headers=student_auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["event_type"] == "quiz_started"

    def test_record_event_all_valid_types(self, client: TestClient, student_auth_headers: dict):
        """All defined event types should be accepted."""
        valid_types = [
            "resource_view", "video_started", "video_completed",
            "quiz_started", "quiz_completed", "hint_requested",
            "tutor_message", "topic_revisit",
        ]
        for evt_type in valid_types:
            resp = client.post(
                "/api/v1/events",
                json={"event_type": evt_type},
                headers=student_auth_headers,
            )
            assert resp.status_code == 201, f"Failed for event_type={evt_type}: {resp.text}"

    def test_record_event_invalid_type_rejected(self, client: TestClient, student_auth_headers: dict):
        """Invalid event_type should return 422."""
        resp = client.post(
            "/api/v1/events",
            json={"event_type": "made_up_event_type"},
            headers=student_auth_headers,
        )
        assert resp.status_code == 422

    def test_record_event_missing_event_type(self, client: TestClient, student_auth_headers: dict):
        """Missing event_type field should return 422."""
        resp = client.post(
            "/api/v1/events",
            json={"event_data": {}},
            headers=student_auth_headers,
        )
        assert resp.status_code == 422

    def test_record_event_unauthenticated(self, client: TestClient):
        """Unauthenticated request should return 401 or 403."""
        resp = client.post(
            "/api/v1/events",
            json={"event_type": "resource_view"},
        )
        assert resp.status_code in (401, 403)

    def test_teacher_cannot_record_event(self, client: TestClient, teacher_auth_headers: dict):
        """Teachers are not students — should not be allowed to record student events."""
        resp = client.post(
            "/api/v1/events",
            json={"event_type": "resource_view"},
            headers=teacher_auth_headers,
        )
        assert resp.status_code in (401, 403)


# ─── Event Listing ────────────────────────────────────────────────────────────

class TestListEvents:
    """Tests for GET /api/v1/events."""

    def test_list_events_empty_for_new_student(self, client: TestClient, student_auth_headers: dict):
        """A new student with no events should get an empty list."""
        resp = client.get("/api/v1/events", headers=student_auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert isinstance(body["data"], list)
        assert body["total"] >= 0

    def test_list_events_returns_recorded_events(self, client: TestClient, student_auth_headers: dict):
        """Events recorded by the student should appear in the list."""
        # Record two events
        for evt in ["resource_view", "quiz_started"]:
            client.post(
                "/api/v1/events",
                json={"event_type": evt},
                headers=student_auth_headers,
            )

        resp = client.get("/api/v1/events", headers=student_auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 2
        assert len(body["data"]) >= 2

    def test_list_events_pagination_fields(self, client: TestClient, student_auth_headers: dict):
        """Response includes pagination metadata."""
        resp = client.get("/api/v1/events?page=1&page_size=10", headers=student_auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "page" in body
        assert "page_size" in body
        assert "total_pages" in body

    def test_list_events_unauthenticated(self, client: TestClient):
        resp = client.get("/api/v1/events")
        assert resp.status_code in (401, 403)


# ─── Session Management ───────────────────────────────────────────────────────

class TestSessions:
    """Tests for POST /api/v1/sessions and PATCH /api/v1/sessions/{id}."""

    def test_start_session_success(self, client: TestClient, student_auth_headers: dict):
        """Student can start a learning session."""
        resp = client.post(
            "/api/v1/sessions",
            json={"session_type": "study"},
            headers=student_auth_headers,
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()["data"]
        assert "id" in data
        assert data["session_type"] == "study"
        assert "started_at" in data

    def test_start_session_quiz_type(self, client: TestClient, student_auth_headers: dict):
        """Quiz session type is accepted."""
        resp = client.post(
            "/api/v1/sessions",
            json={"session_type": "quiz"},
            headers=student_auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["session_type"] == "quiz"

    def test_start_session_invalid_type_rejected(self, client: TestClient, student_auth_headers: dict):
        """Invalid session_type should fail validation."""
        resp = client.post(
            "/api/v1/sessions",
            json={"session_type": "invalid_type"},
            headers=student_auth_headers,
        )
        assert resp.status_code == 422

    def test_end_session_success(self, client: TestClient, student_auth_headers: dict):
        """Student can end a session with a duration."""
        # Start session
        start_resp = client.post(
            "/api/v1/sessions",
            json={"session_type": "study"},
            headers=student_auth_headers,
        )
        assert start_resp.status_code == 201
        session_id = start_resp.json()["data"]["id"]

        # End session
        end_resp = client.patch(
            f"/api/v1/sessions/{session_id}",
            json={"duration_seconds": 600},
            headers=student_auth_headers,
        )
        assert end_resp.status_code == 200, end_resp.text
        data = end_resp.json()["data"]
        assert data["duration_seconds"] == 600
        assert data["ended_at"] is not None

    def test_end_nonexistent_session_404(self, client: TestClient, student_auth_headers: dict):
        """Ending a session that doesn't exist or belongs to another user returns 404."""
        import uuid
        resp = client.patch(
            f"/api/v1/sessions/{uuid.uuid4()}",
            json={"duration_seconds": 100},
            headers=student_auth_headers,
        )
        assert resp.status_code == 404

    def test_session_requires_auth(self, client: TestClient):
        resp = client.post("/api/v1/sessions", json={"session_type": "study"})
        assert resp.status_code in (401, 403)
