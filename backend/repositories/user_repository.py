"""Data access for the User entity.

Services never construct SQLAlchemy queries directly - they go
through this repository. Keeps persistence swappable and testable
in isolation from business logic.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.user import User


class UserRepository:
    def __init__(self, db_session: Session) -> None:
        self._db_session = db_session

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self._db_session.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        return self._db_session.execute(statement).scalar_one_or_none()

    def create(self, *, email: str, hashed_password: str, full_name: str | None) -> User:
        user = User(email=email, hashed_password=hashed_password, full_name=full_name)
        self._db_session.add(user)
        self._db_session.commit()
        self._db_session.refresh(user)
        return user
