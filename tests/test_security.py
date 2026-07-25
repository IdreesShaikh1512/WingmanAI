import uuid

import pytest
from jose import JWTError

from backend.core.security import TokenType, create_token, decode_token, hash_password, verify_password


def test_password_hash_and_verify_roundtrip():
    hashed = hash_password("correct-horse-battery-staple")
    assert verify_password("correct-horse-battery-staple", hashed)
    assert not verify_password("wrong-password", hashed)


def test_access_token_roundtrip():
    user_id = uuid.uuid4()
    token = create_token(user_id, TokenType.ACCESS)
    assert decode_token(token, TokenType.ACCESS) == user_id


def test_token_type_mismatch_is_rejected():
    user_id = uuid.uuid4()
    refresh_token = create_token(user_id, TokenType.REFRESH)
    with pytest.raises(JWTError):
        decode_token(refresh_token, TokenType.ACCESS)
