from typing import Annotated

from fastapi import APIRouter, Depends, status

from api.deps import get_current_user, get_reminder_service
from models.user import User
from schemas.reminder import CreateReminderRequest, ReminderResponse
from services.reminder_service import ReminderService

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.post("", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
def create_reminder(
    payload: CreateReminderRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    reminder_service: Annotated[ReminderService, Depends(get_reminder_service)],
) -> ReminderResponse:
    return reminder_service.create_reminder(current_user.id, payload.title, payload.remind_at)


@router.get("", response_model=list[ReminderResponse])
def list_reminders(
    current_user: Annotated[User, Depends(get_current_user)],
    reminder_service: Annotated[ReminderService, Depends(get_reminder_service)],
) -> list[ReminderResponse]:
    return reminder_service.list_reminders(current_user.id)
