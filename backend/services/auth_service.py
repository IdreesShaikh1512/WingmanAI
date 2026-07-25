"""Auth business logic: registration, login, token refresh.

Routes call this service and nothing else. This is the single
place that coordinates password hashing, repository access, and
token issuance for authentication.
"""

import uuid

from jose import JWTError

from core.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidTokenError,
    UserNotFoundError,
)
from core.security import TokenType, create_token, decode_token, hash_password, verify_password
from models.user import User
from repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    def register(self, *, email: str, password: str, full_name: str | None) -> User:
        if self._user_repository.get_by_email(email) is not None:
            raise EmailAlreadyRegisteredError(email)

        return self._user_repository.create(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
        )

    def authenticate(self, *, email: str, password: str) -> User:
        user = self._user_repository.get_by_email(email)

        if user is None or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()

        if not user.is_active:
            raise InvalidCredentialsError()

        return user

    def issue_tokens(self, user_id: uuid.UUID) -> tuple[str, str]:
        access_token = create_token(user_id, TokenType.ACCESS)
        refresh_token = create_token(user_id, TokenType.REFRESH)
        return access_token, refresh_token

    def refresh_access_token(self, refresh_token: str) -> tuple[str, str]:
        try:
            user_id = decode_token(refresh_token, TokenType.REFRESH)
        except JWTError as error:
            raise InvalidTokenError(str(error)) from error

        user = self._user_repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(str(user_id))

        return self.issue_tokens(user.id)
