import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db
from .base import BaseModel


class CalendarEvent(BaseModel, db.Model):
    """One concrete occurrence of a calendar event, mirrored from CalDAV.

    Single events have recurrence_id "" (empty, not NULL, so the unique
    constraint holds on Postgres). Occurrences of a recurring event carry the
    original occurrence start as an ISO string, which stays stable when the
    occurrence is moved by an override. `task_id` is the X-POZZY-TASK-ID value
    of events Pozzy wrote for a scheduled task (plain UUID, no FK, resolved by
    the caller). Datetimes are stored in UTC.
    """

    __tablename__ = "calendar_events"
    __table_args__ = (UniqueConstraint("calendar_url", "uid", "recurrence_id", name="uq_calendar_events_occurrence"),)

    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("calendar_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    calendar_url: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    uid: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    recurrence_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    etag: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    all_day: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    location: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    task_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True, index=True)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict:
        from ..utils.dates import iso

        return {
            "id": str(self.id),
            "account_id": str(self.account_id),
            "calendar_url": self.calendar_url,
            "uid": self.uid,
            "recurrence_id": self.recurrence_id or None,
            "etag": self.etag,
            "title": self.title,
            "start": iso(self.start),
            "end": iso(self.end),
            "all_day": self.all_day,
            "location": self.location,
            "description": self.description,
            "task_id": str(self.task_id) if self.task_id else None,
            "last_synced_at": iso(self.last_synced_at),
        }
