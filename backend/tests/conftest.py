"""
pytest configuration and shared fixtures.
Uses an in-memory SQLite DB for fast unit tests.
Integration tests can override with real PostgreSQL.
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use test database URL
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SECRET_KEY"] = "test_secret_key_for_testing_only"
os.environ["JWT_SECRET_KEY"] = "test_jwt_secret_key_for_testing_only_must_be_long_enough"
os.environ["LLM_PROVIDER"] = "local"  # No real LLM calls in unit tests

from app.core.database import Base, get_db
from app.main import app


# ─── Test Database ────────────────────────────────────────────────────────────
TEST_DB_URL = "sqlite:///./test.db"

test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """Create all tables once per test session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    """Provide a clean DB session for each test with rollback."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """FastAPI test client with overridden DB dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ─── Test Data Factories ──────────────────────────────────────────────────────
@pytest.fixture
def student_credentials():
    return {
        "email": "student@test.com",
        "password": "testpassword123",
        "full_name": "Test Student",
        "role": "student",
    }


@pytest.fixture
def teacher_credentials():
    return {
        "email": "teacher@test.com",
        "password": "testpassword123",
        "full_name": "Test Teacher",
        "role": "teacher",
    }


@pytest.fixture
def registered_student(client, student_credentials):
    """Register a student and return the token response."""
    response = client.post("/api/v1/auth/register", json=student_credentials)
    assert response.status_code == 201
    return response.json()["data"]


@pytest.fixture
def registered_teacher(client, teacher_credentials):
    """Register a teacher and return the token response."""
    response = client.post("/api/v1/auth/register", json=teacher_credentials)
    assert response.status_code == 201
    return response.json()["data"]


@pytest.fixture
def student_auth_headers(registered_student):
    """Authorization headers for a registered student."""
    return {"Authorization": f"Bearer {registered_student['access_token']}"}


@pytest.fixture
def teacher_auth_headers(registered_teacher):
    """Authorization headers for a registered teacher."""
    return {"Authorization": f"Bearer {registered_teacher['access_token']}"}
