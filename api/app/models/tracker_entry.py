import uuid
from datetime import date
from typing import Optional

from sqlalchemy import Date, Float, ForeignKey, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db
from .base import BaseModel


class TrackerEntry(BaseModel, db.Model):
    __tablename__ = "tracker_entries"
    __table_args__ = (UniqueConstraint("tracker_id", "date", name="uq_tracker_entries_tracker_date"),)

    tracker_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("trackers.id", ondelete="CASCADE"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def to_dict(self) -> dict:
        return {"id": str(self.id), "tracker_id": str(self.tracker_id), "date": self.date.isoformat(), "value": self.value, "note": self.note}
