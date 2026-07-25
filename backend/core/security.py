"""Security primitives: password hashing and JWT handling.

Nothing outside this module should call passlib or jose directly.
Keeps the cryptographic surface area in one auditable place.

Hashing uses argon2 when argon2-cffi is installed (preferred), and
falls back to bcrypt automatically so the app stays runnable in
minimal environments. Both backends are declared in pyproject.toml.
"""

import uuid
from datetime import datetime, timedelta, timezone
from enum import StrEnum

from jose import JWTError, jwt
from passlib.context import CryptContext

from config.settings import get_settings

settings = get_settings()

# Try argon2 first; fall back to bcrypt if argon2-cffi is not available.
# This prevents a MissingBackendError 500 on every register/login call
# when running in environments without the argon2-cffi C extension.
try:
    from argon2 import PasswordHasher  # noqa: F401 – just a probe import

    _pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
except ImportError:
    _pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


def hash_password(plain_password: str) -> str:
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _pwd_context.verify(plain_password, hashed_password)


def create_token(user_id: uuid.UUID, token_type: TokenType) -> str:
    if token_type == TokenType.ACCESS:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    else:
        expires_delta = timedelta(days=settings.refresh_token_expire_days)

    expire = datetime.now(timezone.utc) + expires_delta
    payload = {"sub": str(user_id), "type": token_type.value, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str, expected_type: TokenType) -> uuid.UUID:
    """Decode and validate a JWT. Raises JWTError on any failure."""
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])

    if payload.get("type") != expected_type.value:
        raise JWTError(f"Expected {expected_type.value} token, got {payload.get('type')}")

    return uuid.UUID(payload["sub"])
