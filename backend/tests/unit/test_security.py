"""
Unit tests for security utility functions.
Tests: password hashing, JWT creation/decoding.
"""
import pytest
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.exceptions import UnauthorizedException


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        hashed = hash_password("mypassword123")
        assert hashed != "mypassword123"

    def test_verify_correct_password(self):
        hashed = hash_password("mypassword123")
        assert verify_password("mypassword123", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("mypassword123")
        assert verify_password("wrongpassword", hashed) is False

    def test_two_hashes_of_same_password_differ(self):
        # bcrypt uses random salt — same password → different hash
        h1 = hash_password("samepassword")
        h2 = hash_password("samepassword")
        assert h1 != h2


class TestJWTTokens:
    def test_access_token_creation_and_decoding(self):
        user_id = "test-user-id"
        token = create_access_token(user_id, "student")
        payload = decode_token(token)
        assert payload["sub"] == user_id
        assert payload["role"] == "student"
        assert payload["type"] == "access"

    def test_refresh_token_type_is_refresh(self):
        token = create_refresh_token("test-user-id", "teacher")
        payload = decode_token(token)
        assert payload["type"] == "refresh"

    def test_invalid_token_raises_unauthorized(self):
        with pytest.raises(UnauthorizedException):
            decode_token("invalid.jwt.token")

    def test_tampered_token_raises_unauthorized(self):
        token = create_access_token("user-id", "student")
        # Tamper with the token
        parts = token.split(".")
        tampered = parts[0] + "." + parts[1] + ".invalidsignature"
        with pytest.raises(UnauthorizedException):
            decode_token(tampered)
