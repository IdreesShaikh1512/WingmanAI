import uuid
from datetime import datetime

from models.reminder import Reminder
from repositories.reminder_repository import ReminderRepository


class ReminderService:
    def __init__(self, reminder_repository: ReminderRepository) -> None:
        self._reminder_repository = reminder_repository

    def create_reminder(self, user_id: uuid.UUID, title: str, remind_at: datetime) -> Reminder:
        return self._reminder_repository.create(user_id=user_id, title=title, remind_at=remind_at)

    def list_reminders(self, user_id: uuid.UUID) -> list[Reminder]:
        return self._reminder_repository.list_for_user(user_id)
