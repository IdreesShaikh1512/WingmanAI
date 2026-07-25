import uuid
from datetime import date

from models.trip import Trip
from repositories.trip_repository import TripRepository


class TripService:
    def __init__(self, trip_repository: TripRepository) -> None:
        self._trip_repository = trip_repository

    def create_trip(
        self, user_id: uuid.UUID, destination: str, start_date: date | None, end_date: date | None, budget: float | None
    ) -> Trip:
        return self._trip_repository.create(
            user_id=user_id, destination=destination, start_date=start_date, end_date=end_date, budget=budget
        )

    def list_trips(self, user_id: uuid.UUID) -> list[Trip]:
        return self._trip_repository.list_for_user(user_id)
