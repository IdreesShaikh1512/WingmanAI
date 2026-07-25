"""User entity.

Owns identity and credentials only. Profile/preference data that
grows independently of auth concerns should live in a separate
Settings/Profile table referencing this one, not bolted on here.
"""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from database.base import TimestampedEntity


class User(TimestampedEntity):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
