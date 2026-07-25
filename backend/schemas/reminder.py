import uuid
from datetime import datetime

from pydantic import BaseModel


class CreateReminderRequest(BaseModel):
    title: str
    remind_at: datetime


class ReminderResponse(BaseModel):
    id: uuid.UUID
    title: str
    remind_at: datetime
    is_sent: bool

    model_config = {"from_attributes": True}
