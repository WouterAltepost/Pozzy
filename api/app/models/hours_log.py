import uuid
from datetime import date
from typing import Optional

from sqlalchemy import Date, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db
from .base import BaseModel, JSONType


class HoursLog(BaseModel, db.Model):
    __tablename__ = "hours_logs"

    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    area_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("areas.id"), nullable=True, index=True)
    tags: Mapped[list] = mapped_column(JSONType, nullable=False, default=list)
    minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    task_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    # What the log was made from ("event:<uid>|<recurrence_id>" or "task:<id>"), so the hours
    # suggestions never offer the same agenda event or completed task twice.
    source_ref: Mapped[Optional[str]] = mapped_column(String(400), nullable=True, index=True)

    def to_dict(self) -> dict:
        from ..utils.dates import iso

        return {
            "id": str(self.id),
            "date": self.date.isoformat(),
            "area_id": str(self.area_id) if self.area_id else None,
            "tags": list(self.tags or []),
            "minutes": self.minutes,
            "note": self.note,
            "task_id": str(self.task_id) if self.task_id else None,
            "source_ref": self.source_ref,
            "created_at": iso(self.created_at),
        }


class HoursDismissal(BaseModel, db.Model):
    """A suggested hours entry the user chose not to log, keyed by the suggestion's ref."""

    __tablename__ = "hours_dismissals"

    ref: Mapped[str] = mapped_column(String(400), nullable=False, unique=True)
