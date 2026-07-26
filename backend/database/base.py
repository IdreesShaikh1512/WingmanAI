"""Declarative base and shared entity mixin.

Every table in Wingman must use a UUID primary key and track
created_at / updated_at. Cross-database compatible (PostgreSQL + SQLite fallback).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampedEntity(Base):
    """Abstract base providing id, created_at, updated_at for all entities."""

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
