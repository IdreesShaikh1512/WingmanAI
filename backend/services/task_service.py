import uuid
from datetime import datetime

from models.task import Task
from repositories.task_repository import TaskRepository


class TaskService:
    def __init__(self, task_repository: TaskRepository) -> None:
        self._task_repository = task_repository

    def create_task(
        self, user_id: uuid.UUID, title: str, description: str | None, due_date: datetime | None
    ) -> Task:
        return self._task_repository.create(user_id=user_id, title=title, description=description, due_date=due_date)

    def list_tasks(self, user_id: uuid.UUID) -> list[Task]:
        return self._task_repository.list_for_user(user_id)

    def update_status(self, task_id: uuid.UUID, user_id: uuid.UUID, status: str) -> Task:
        task = self._task_repository.get(task_id, user_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")
        return self._task_repository.update_status(task, status)
