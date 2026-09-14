import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db
from .base import BaseModel, JSONType


class CalendarAccount(BaseModel, db.Model):
    """One CalDAV account (v1: the single iCloud account from env).

    `secret_ref` names the environment variable holding the app password; the
    password itself is never stored. `calendar_urls` is the list of calendars
    that are synced. `write_calendar_url` is where Pozzy creates events.
    `known_calendars` caches the last discovery ([{name, url}]) so the Settings
    page can render choices without a live call.
    """

    __tablename__ = "calendar_accounts"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    caldav_url: Mapped[str] = mapped_column(String(500), nullable=False)
    username: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    secret_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    calendar_urls: Mapped[list] = mapped_column(JSONType, nullable=False, default=list)
    write_calendar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    known_calendars: Mapped[list] = mapped_column(JSONType, nullable=False, default=list)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def to_dict(self) -> dict:
        from ..utils.dates import iso

        return {
            "id": str(self.id),
            "name": self.name,
            "caldav_url": self.caldav_url,
            "username": self.username,
            "secret_ref": self.secret_ref,
            "calendar_urls": list(self.calendar_urls or []),
            "write_calendar_url": self.write_calendar_url,
            "known_calendars": list(self.known_calendars or []),
            "enabled": self.enabled,
            "last_synced_at": iso(self.last_synced_at),
            "last_sync_error": self.last_sync_error,
        }
