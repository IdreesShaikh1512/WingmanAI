import uuid

import pytest

from backend.core.exceptions import EmailAlreadyRegisteredError, InvalidCredentialsError
from backend.core.security import hash_password
from backend.models.user import User
from backend.services.auth_service import AuthService


class FakeUserRepository:
    """In-memory stand-in for UserRepository, used to unit test AuthService in isolation."""

    def __init__(self):
        self._users_by_email: dict[str, User] = {}

    def get_by_email(self, email: str) -> User | None:
        return self._users_by_email.get(email)

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return next((u for u in self._users_by_email.values() if u.id == user_id), None)

    def create(self, *, email: str, hashed_password: str, full_name: str | None) -> User:
        user = User(id=uuid.uuid4(), email=email, hashed_password=hashed_password, full_name=full_name)
        user.is_active = True
        self._users_by_email[email] = user
        return user


@pytest.fixture
def auth_service() -> AuthService:
    return AuthService(FakeUserRepository())


def test_register_creates_user_with_hashed_password(auth_service):
    user = auth_service.register(email="a@example.com", password="password123", full_name="Ada")
    assert user.email == "a@example.com"
    assert user.hashed_password != "password123"


def test_register_rejects_duplicate_email(auth_service):
    auth_service.register(email="a@example.com", password="password123", full_name=None)
    with pytest.raises(EmailAlreadyRegisteredError):
        auth_service.register(email="a@example.com", password="anotherpass", full_name=None)


def test_authenticate_succeeds_with_correct_password(auth_service):
    auth_service.register(email="a@example.com", password="password123", full_name=None)
    user = auth_service.authenticate(email="a@example.com", password="password123")
    assert user.email == "a@example.com"


def test_authenticate_rejects_wrong_password(auth_service):
    auth_service.register(email="a@example.com", password="password123", full_name=None)
    with pytest.raises(InvalidCredentialsError):
        auth_service.authenticate(email="a@example.com", password="wrong-password")


def test_authenticate_rejects_unknown_email(auth_service):
    with pytest.raises(InvalidCredentialsError):
        auth_service.authenticate(email="nobody@example.com", password="whatever")
