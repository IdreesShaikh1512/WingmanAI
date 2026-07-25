from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from api.deps import get_chat_service, get_current_user
from models.user import User
from schemas.chat import ChatResponse, MessageResponse, SendMessageRequest
from services.chat_service import ChatService

router = APIRouter(prefix="/chats", tags=["chats"])


@router.post("", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
def create_chat(
    current_user: Annotated[User, Depends(get_current_user)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
) -> ChatResponse:
    return chat_service.start_chat(current_user.id)


@router.get("", response_model=list[ChatResponse])
def list_chats(
    current_user: Annotated[User, Depends(get_current_user)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
) -> list[ChatResponse]:
    return chat_service.list_chats(current_user.id)


@router.post("/{chat_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(
    chat_id: uuid.UUID,
    payload: SendMessageRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
) -> MessageResponse:
    try:
        return chat_service.send_message(chat_id, current_user.id, payload.content)
    except ValueError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(error)) from error
