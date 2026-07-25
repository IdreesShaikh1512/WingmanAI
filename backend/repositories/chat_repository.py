import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.chat import Chat, Message


class ChatRepository:
    def __init__(self, db_session: Session) -> None:
        self._db_session = db_session

    def create_chat(self, user_id: uuid.UUID, title: str = "New Chat") -> Chat:
        chat = Chat(user_id=user_id, title=title)
        self._db_session.add(chat)
        self._db_session.commit()
        self._db_session.refresh(chat)
        return chat

    def get_chat(self, chat_id: uuid.UUID, user_id: uuid.UUID) -> Chat | None:
        statement = select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
        return self._db_session.execute(statement).scalar_one_or_none()

    def list_chats(self, user_id: uuid.UUID) -> list[Chat]:
        statement = select(Chat).where(Chat.user_id == user_id).order_by(Chat.created_at.desc())
        return list(self._db_session.execute(statement).scalars().all())

    def add_message(
        self, chat_id: uuid.UUID, role: str, content: str, agent_metadata: dict | None = None
    ) -> Message:
        message = Message(chat_id=chat_id, role=role, content=content, agent_metadata=agent_metadata)
        self._db_session.add(message)
        self._db_session.commit()
        self._db_session.refresh(message)
        return message
