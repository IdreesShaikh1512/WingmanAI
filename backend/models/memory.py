"""Memory entity."""

import uuid

from sqlalchemy import ForeignKey, String, Text, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import TimestampedEntity


class Memory(TimestampedEntity):
    __tablename__ = "memories"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)  # chat | document | manual
    memory_type: Mapped[str] = mapped_column(String(50), default="general")  # general | travel | task | personal
