"""Trip entity."""

import uuid
from datetime import date

from sqlalchemy import JSON, Date, ForeignKey, Numeric, String, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import TimestampedEntity


class Trip(TimestampedEntity):
    __tablename__ = "trips"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    destination: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    budget: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    itinerary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="planning")  # planning | booked | completed
