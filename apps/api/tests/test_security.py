"""Unit tests for password hashing and JWT."""

from uuid import uuid4

import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_and_verify_password():
    hashed = hash_password("SecurePass123!")
    assert hashed != "SecurePass123!"
    assert verify_password("SecurePass123!", hashed)
    assert not verify_password("wrong", hashed)


def test_access_token_roundtrip():
    user_id = uuid4()
    token = create_access_token(user_id, extra_claims={"email": "test@example.com"})
    payload = decode_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"
    assert payload["email"] == "test@example.com"
    assert "exp" in payload


def test_refresh_token_type():
    user_id = uuid4()
    token = create_refresh_token(user_id)
    payload = decode_token(token)
    assert payload["type"] == "refresh"
    assert payload["sub"] == str(user_id)


def test_invalid_token_raises():
    with pytest.raises(ValueError):
        decode_token("not.a.valid.token")
