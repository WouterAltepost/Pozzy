import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db
from .base import BaseModel, JSONType

TASK_STATUSES = ("inbox", "todo", "scheduled", "done", "dropped")
TASK_SOURCES = ("manual", "capture", "email", "three_do")


class Task(BaseModel, db.Model):
    """Shared table (stream A owns it). B, C and D read and update columns but never alter it."""

    __tablename__ = "tasks"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    area_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("areas.id"), nullable=True, index=True)
    # JSON array of strings instead of Postgres text[] so SQLite tests work.
    tags: Mapped[list] = mapped_column(JSONType, nullable=False, default=list)
    urgent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    important: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="todo", index=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    estimated_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    scheduled_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    scheduled_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    calendar_uid: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")
    source_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    @property
    def quadrant(self) -> str:
        if self.urgent and self.important:
            return "do"
        if self.important:
            return "schedule"
        if self.urgent:
            return "delegate"
        return "eliminate"

    def to_dict(self) -> dict:
        from ..utils.dates import iso

        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "area_id": str(self.area_id) if self.area_id else None,
            "tags": list(self.tags or []),
            "urgent": self.urgent,
            "important": self.important,
            "quadrant": self.quadrant,
            "status": self.status,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "estimated_minutes": self.estimated_minutes,
            "scheduled_start": iso(self.scheduled_start),
            "scheduled_end": iso(self.scheduled_end),
            "calendar_uid": self.calendar_uid,
            "completed_at": iso(self.completed_at),
            "source": self.source,
            "source_ref": self.source_ref,
            "created_at": iso(self.created_at),
            "updated_at": iso(self.updated_at),
        }
