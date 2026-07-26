"""Task entity."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import TimestampedEntity


class Task(TimestampedEntity):
    __tablename__ = "tasks"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    chat_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("chats.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | in_progress | done | cancelled
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
