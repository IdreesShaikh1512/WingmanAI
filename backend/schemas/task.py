import uuid
from datetime import datetime

from pydantic import BaseModel


class CreateTaskRequest(BaseModel):
    title: str
    description: str | None = None
    due_date: datetime | None = None


class UpdateTaskStatusRequest(BaseModel):
    status: str


class TaskResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    status: str
    due_date: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
