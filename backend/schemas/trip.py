import uuid
from datetime import date

from pydantic import BaseModel


class CreateTripRequest(BaseModel):
    destination: str
    start_date: date | None = None
    end_date: date | None = None
    budget: float | None = None


class TripResponse(BaseModel):
    id: uuid.UUID
    destination: str
    start_date: date | None
    end_date: date | None
    budget: float | None
    itinerary: dict | None
    status: str

    model_config = {"from_attributes": True}
