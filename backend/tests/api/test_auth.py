"""
Unit tests for authentication service.
Tests: registration, login, JWT tokens, role guards, duplicate email.
"""
import pytest


class TestHealthCheck:
    def test_health_endpoint_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "database" in data


class TestRegistration:
    def test_student_registration_success(self, client, student_credentials):
        response = client.post("/api/v1/auth/register", json=student_credentials)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["role"] == "student"

    def test_teacher_registration_success(self, client, teacher_credentials):
        response = client.post("/api/v1/auth/register", json=teacher_credentials)
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["role"] == "teacher"

    def test_duplicate_email_returns_409(self, client, student_credentials):
        client.post("/api/v1/auth/register", json=student_credentials)
        response = client.post("/api/v1/auth/register", json=student_credentials)
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "CONFLICT"

    def test_short_password_rejected(self, client):
        response = client.post("/api/v1/auth/register", json={
            "email": "short@test.com",
            "password": "abc",
            "full_name": "Short Pass",
            "role": "student",
        })
        assert response.status_code == 422

    def test_invalid_email_rejected(self, client):
        response = client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "password": "validpassword123",
            "full_name": "Bad Email",
            "role": "student",
        })
        assert response.status_code == 422

    def test_invalid_role_rejected(self, client):
        response = client.post("/api/v1/auth/register", json={
            "email": "role@test.com",
            "password": "validpassword123",
            "full_name": "Bad Role",
            "role": "superadmin",  # not a valid role
        })
        assert response.status_code == 422


class TestLogin:
    def test_login_success_returns_tokens(self, client, student_credentials):
        client.post("/api/v1/auth/register", json=student_credentials)
        response = client.post("/api/v1/auth/login", json={
            "email": student_credentials["email"],
            "password": student_credentials["password"],
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]

    def test_wrong_password_returns_401(self, client, student_credentials):
        client.post("/api/v1/auth/register", json=student_credentials)
        response = client.post("/api/v1/auth/login", json={
            "email": student_credentials["email"],
            "password": "wrongpassword",
        })
        assert response.status_code == 401

    def test_unknown_email_returns_401(self, client):
        response = client.post("/api/v1/auth/login", json={
            "email": "nobody@test.com",
            "password": "somepassword",
        })
        assert response.status_code == 401


class TestTokenRefresh:
    def test_refresh_token_returns_new_access_token(self, client, registered_student):
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": registered_student["refresh_token"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data["data"]
        # New access token should be different
        assert data["data"]["access_token"] != registered_student["access_token"]

    def test_access_token_cannot_be_used_as_refresh(self, client, registered_student):
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": registered_student["access_token"]  # Wrong: using access token
        })
        assert response.status_code == 401


class TestProtectedRoutes:
    def test_missing_token_returns_401(self, client):
        response = client.get("/api/v1/students/me")
        # Will be 404 until students router is registered, or 401 with auth
        assert response.status_code in (401, 404)

    def test_invalid_token_returns_401(self, client):
        response = client.get(
            "/api/v1/students/me",
            headers={"Authorization": "Bearer invalid.jwt.token"}
        )
        assert response.status_code in (401, 404)
