import uuid
from datetime import date
from typing import Optional

from sqlalchemy import Date, Float, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db
from .base import BaseModel

# done: the value counts. skipped: the day was excused (ill, travelling); it neither counts
# nor breaks a streak, and its value is 0.
ENTRY_STATUSES = ("done", "skipped")


class TrackerEntry(BaseModel, db.Model):
    __tablename__ = "tracker_entries"
    __table_args__ = (UniqueConstraint("tracker_id", "date", name="uq_tracker_entries_tracker_date"),)

    tracker_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("trackers.id", ondelete="CASCADE"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="done", server_default="done")

    @property
    def skipped(self) -> bool:
        return self.status == "skipped"

    def to_dict(self) -> dict:
        return {"id": str(self.id), "tracker_id": str(self.tracker_id), "date": self.date.isoformat(), "value": self.value, "note": self.note, "status": self.status or "done"}
