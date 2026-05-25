"""Tests for JWT authentication middleware."""

import uuid

import pytest

from app.middleware.auth import create_access_token, decode_access_token
from app.middleware.error_handler import Unauthorized


def test_create_and_decode_token():
    """Test token creation and decoding round-trip."""
    user_id = str(uuid.uuid4())
    token = create_access_token(user_id)
    payload = decode_access_token(token)
    assert payload["sub"] == user_id


def test_decode_invalid_token():
    """Test that invalid tokens raise Unauthorized."""
    with pytest.raises(Unauthorized):
        decode_access_token("invalid-token")


def test_decode_empty_token():
    """Test that empty tokens raise Unauthorized."""
    with pytest.raises(Unauthorized):
        decode_access_token("")


def test_token_contains_required_fields():
    """Test that tokens contain sub, exp, iat, jti."""
    user_id = str(uuid.uuid4())
    token = create_access_token(user_id)
    payload = decode_access_token(token)
    assert "sub" in payload
    assert "exp" in payload
    assert "iat" in payload
    assert "jti" in payload
