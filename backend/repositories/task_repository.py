import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.task import Task


class TaskRepository:
    def __init__(self, db_session: Session) -> None:
        self._db_session = db_session

    def create(
        self,
        user_id: uuid.UUID,
        title: str,
        description: str | None = None,
        due_date: datetime | None = None,
        chat_id: uuid.UUID | None = None,
    ) -> Task:
        task = Task(user_id=user_id, title=title, description=description, due_date=due_date, chat_id=chat_id)
        self._db_session.add(task)
        self._db_session.commit()
        self._db_session.refresh(task)
        return task

    def list_for_user(self, user_id: uuid.UUID) -> list[Task]:
        statement = select(Task).where(Task.user_id == user_id).order_by(Task.created_at.desc())
        return list(self._db_session.execute(statement).scalars().all())

    def get(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Task | None:
        statement = select(Task).where(Task.id == task_id, Task.user_id == user_id)
        return self._db_session.execute(statement).scalar_one_or_none()

    def update_status(self, task: Task, status: str) -> Task:
        task.status = status
        self._db_session.commit()
        self._db_session.refresh(task)
        return task
