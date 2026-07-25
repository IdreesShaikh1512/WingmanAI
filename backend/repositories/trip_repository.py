import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.trip import Trip


class TripRepository:
    def __init__(self, db_session: Session) -> None:
        self._db_session = db_session

    def create(
        self,
        user_id: uuid.UUID,
        destination: str,
        start_date: date | None,
        end_date: date | None,
        budget: float | None,
    ) -> Trip:
        trip = Trip(
            user_id=user_id, destination=destination, start_date=start_date, end_date=end_date, budget=budget
        )
        self._db_session.add(trip)
        self._db_session.commit()
        self._db_session.refresh(trip)
        return trip

    def list_for_user(self, user_id: uuid.UUID) -> list[Trip]:
        statement = select(Trip).where(Trip.user_id == user_id).order_by(Trip.created_at.desc())
        return list(self._db_session.execute(statement).scalars().all())
