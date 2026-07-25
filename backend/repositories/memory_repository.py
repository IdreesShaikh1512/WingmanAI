"""Memory Repository.

Simple data-access layer for the memories table.
Keeps DB queries out of MemoryManager so the persistence layer stays swappable.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.memory import Memory


class MemoryRepository:
    def __init__(self, db_session: Session) -> None:
        self._db_session = db_session

    def create(
        self,
        user_id: uuid.UUID,
        content: str,
        source: str = "chat",
        memory_type: str = "general",
    ) -> Memory:
        memory = Memory(
            user_id=user_id,
            content=content,
            source=source,
            memory_type=memory_type,
        )
        self._db_session.add(memory)
        self._db_session.commit()
        self._db_session.refresh(memory)
        return memory

    def list_for_user(
        self,
        user_id: uuid.UUID,
        memory_type: str | None = None,
        limit: int = 50,
    ) -> list[Memory]:
        stmt = select(Memory).where(Memory.user_id == user_id)
        if memory_type:
            stmt = stmt.where(Memory.memory_type == memory_type)
        stmt = stmt.order_by(Memory.created_at.desc()).limit(limit)
        return list(self._db_session.execute(stmt).scalars().all())

    def delete_for_user(self, user_id: uuid.UUID) -> int:
        memories = self.list_for_user(user_id, limit=1000)
        for m in memories:
            self._db_session.delete(m)
        self._db_session.commit()
        return len(memories)
