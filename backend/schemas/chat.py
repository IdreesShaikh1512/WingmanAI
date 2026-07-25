import uuid
from datetime import datetime

from pydantic import BaseModel


class SendMessageRequest(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    agent_metadata: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    id: uuid.UUID
    title: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatWithMessagesResponse(ChatResponse):
    messages: list[MessageResponse]
