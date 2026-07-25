import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.reminder import Reminder


class ReminderRepository:
    def __init__(self, db_session: Session) -> None:
        self._db_session = db_session

    def create(self, user_id: uuid.UUID, title: str, remind_at: datetime) -> Reminder:
        reminder = Reminder(user_id=user_id, title=title, remind_at=remind_at)
        self._db_session.add(reminder)
        self._db_session.commit()
        self._db_session.refresh(reminder)
        return reminder

    def list_for_user(self, user_id: uuid.UUID) -> list[Reminder]:
        statement = select(Reminder).where(Reminder.user_id == user_id).order_by(Reminder.remind_at.asc())
        return list(self._db_session.execute(statement).scalars().all())
