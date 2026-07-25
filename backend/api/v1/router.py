"""Aggregates all v1 routers. New feature routers get registered here only."""

from fastapi import APIRouter

from api.v1.auth import router as auth_router
from api.v1.chats import router as chats_router
from api.v1.reminders import router as reminders_router
from api.v1.tasks import router as tasks_router
from api.v1.trips import router as trips_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(chats_router)
api_v1_router.include_router(tasks_router)
api_v1_router.include_router(trips_router)
api_v1_router.include_router(reminders_router)
