from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from api.deps import get_current_user, get_task_service
from models.user import User
from schemas.task import CreateTaskRequest, TaskResponse, UpdateTaskStatusRequest
from services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: CreateTaskRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    task_service: Annotated[TaskService, Depends(get_task_service)],
) -> TaskResponse:
    return task_service.create_task(current_user.id, payload.title, payload.description, payload.due_date)


@router.get("", response_model=list[TaskResponse])
def list_tasks(
    current_user: Annotated[User, Depends(get_current_user)],
    task_service: Annotated[TaskService, Depends(get_task_service)],
) -> list[TaskResponse]:
    return task_service.list_tasks(current_user.id)


@router.patch("/{task_id}/status", response_model=TaskResponse)
def update_task_status(
    task_id: uuid.UUID,
    payload: UpdateTaskStatusRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    task_service: Annotated[TaskService, Depends(get_task_service)],
) -> TaskResponse:
    try:
        return task_service.update_status(task_id, current_user.id, payload.status)
    except ValueError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(error)) from error
