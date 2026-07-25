"""Shared FastAPI dependencies: DB session, service instances, current user.

Centralizing dependency wiring here keeps routes declarative and
makes swapping implementations (e.g. mocking the repository in
tests) a one-line change.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from agents.information_gatekeeper import InformationGatekeeper
from agents.intent_router import IntentRouter
from agents.memory_manager import MemoryManager
from agents.next_action_advisor import NextActionAdvisor
from agents.planner_agent import PlannerAgent
from core.security import TokenType, decode_token
from database.session import get_db_session
from models.user import User
from repositories.chat_repository import ChatRepository
from repositories.memory_repository import MemoryRepository
from repositories.reminder_repository import ReminderRepository
from repositories.task_repository import TaskRepository
from repositories.trip_repository import TripRepository
from repositories.user_repository import UserRepository
from services.auth_service import AuthService
from services.chat_service import ChatService
from services.reminder_service import ReminderService
from services.task_service import TaskService
from services.trip_service import TripService

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ---------------------------------------------------------------------------
# Repositories
# ---------------------------------------------------------------------------

def get_user_repository(
    db_session: Annotated[Session, Depends(get_db_session)],
) -> UserRepository:
    return UserRepository(db_session)


def get_task_repository(db_session: Annotated[Session, Depends(get_db_session)]) -> TaskRepository:
    return TaskRepository(db_session)


def get_trip_repository(db_session: Annotated[Session, Depends(get_db_session)]) -> TripRepository:
    return TripRepository(db_session)


def get_reminder_repository(db_session: Annotated[Session, Depends(get_db_session)]) -> ReminderRepository:
    return ReminderRepository(db_session)


def get_chat_repository(db_session: Annotated[Session, Depends(get_db_session)]) -> ChatRepository:
    return ChatRepository(db_session)


def get_memory_repository(db_session: Annotated[Session, Depends(get_db_session)]) -> MemoryRepository:
    return MemoryRepository(db_session)


# ---------------------------------------------------------------------------
# Services (non-chat)
# ---------------------------------------------------------------------------

def get_auth_service(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> AuthService:
    return AuthService(user_repository)


def get_task_service(
    task_repository: Annotated[TaskRepository, Depends(get_task_repository)],
) -> TaskService:
    return TaskService(task_repository)


def get_trip_service(
    trip_repository: Annotated[TripRepository, Depends(get_trip_repository)],
) -> TripService:
    return TripService(trip_repository)


def get_reminder_service(
    reminder_repository: Annotated[ReminderRepository, Depends(get_reminder_repository)],
) -> ReminderService:
    return ReminderService(reminder_repository)


# ---------------------------------------------------------------------------
# Intelligence Agents (stateless — created per request)
# ---------------------------------------------------------------------------

def get_planner_agent() -> PlannerAgent:
    return PlannerAgent()


def get_intent_router() -> IntentRouter:
    return IntentRouter()


def get_gatekeeper() -> InformationGatekeeper:
    return InformationGatekeeper()


def get_next_action_advisor() -> NextActionAdvisor:
    return NextActionAdvisor()


def get_memory_manager(
    memory_repository: Annotated[MemoryRepository, Depends(get_memory_repository)],
) -> MemoryManager:
    return MemoryManager(memory_repository)


# ---------------------------------------------------------------------------
# Chat Service — full orchestration pipeline
# ---------------------------------------------------------------------------

def get_chat_service(
    chat_repository: Annotated[ChatRepository, Depends(get_chat_repository)],
    task_repository: Annotated[TaskRepository, Depends(get_task_repository)],
    trip_repository: Annotated[TripRepository, Depends(get_trip_repository)],
    reminder_repository: Annotated[ReminderRepository, Depends(get_reminder_repository)],
    planner_agent: Annotated[PlannerAgent, Depends(get_planner_agent)],
    intent_router: Annotated[IntentRouter, Depends(get_intent_router)],
    gatekeeper: Annotated[InformationGatekeeper, Depends(get_gatekeeper)],
    memory_manager: Annotated[MemoryManager, Depends(get_memory_manager)],
    next_action_advisor: Annotated[NextActionAdvisor, Depends(get_next_action_advisor)],
) -> ChatService:
    return ChatService(
        chat_repository=chat_repository,
        task_repository=task_repository,
        trip_repository=trip_repository,
        reminder_repository=reminder_repository,
        planner_agent=planner_agent,
        intent_router=intent_router,
        gatekeeper=gatekeeper,
        memory_manager=memory_manager,
        next_action_advisor=next_action_advisor,
    )


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def get_current_user(
    token: Annotated[str, Depends(_oauth2_scheme)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        user_id = decode_token(token, TokenType.ACCESS)
    except JWTError as error:
        raise credentials_error from error

    user = user_repository.get_by_id(user_id)
    if user is None or not user.is_active:
        raise credentials_error

    return user
