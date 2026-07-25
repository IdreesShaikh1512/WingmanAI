from typing import Annotated

from fastapi import APIRouter, Depends, status

from api.deps import get_current_user, get_trip_service
from models.user import User
from schemas.trip import CreateTripRequest, TripResponse
from services.trip_service import TripService

router = APIRouter(prefix="/trips", tags=["trips"])


@router.post("", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
def create_trip(
    payload: CreateTripRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    trip_service: Annotated[TripService, Depends(get_trip_service)],
) -> TripResponse:
    return trip_service.create_trip(
        current_user.id, payload.destination, payload.start_date, payload.end_date, payload.budget
    )


@router.get("", response_model=list[TripResponse])
def list_trips(
    current_user: Annotated[User, Depends(get_current_user)],
    trip_service: Annotated[TripService, Depends(get_trip_service)],
) -> list[TripResponse]:
    return trip_service.list_trips(current_user.id)
