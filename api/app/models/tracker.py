import uuid
from datetime import date
from typing import Optional

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db
from .base import BaseModel

TRACKER_TYPES = ("daily_bool", "weekly_count", "numeric", "duration")
TARGET_PERIODS = ("day", "week")
# When a day-period habit is due: every day, on the weekdays in `schedule_days` (bitmask,
# Monday is bit 0), or again `schedule_n` days after it was last done. Week-period habits
# (weekly_count, or a target per week) ignore the schedule: any day of the week counts.
SCHEDULES = ("daily", "weekdays", "every_n_days")
ALL_DAYS = 0b1111111


class Tracker(BaseModel, db.Model):
    __tablename__ = "trackers"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    area_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("areas.id"), nullable=True, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    target_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    target_period: Mapped[str] = mapped_column(String(10), nullable=False, default="day")
    unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    schedule: Mapped[str] = mapped_column(String(20), nullable=False, default="daily", server_default="daily")
    schedule_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    schedule_n: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    # "HH:MM" local time for a push reminder; null means no reminder.
    reminder_time: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    # Day the reminder was last sent, so the job sends at most one per habit per day.
    last_reminded_on: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "area_id": str(self.area_id) if self.area_id else None,
            "type": self.type,
            "target_value": self.target_value,
            "target_period": self.target_period,
            "unit": self.unit,
            "active": self.active,
            "sort_order": self.sort_order,
            "schedule": self.schedule or "daily",
            "schedule_days": self.schedule_days,
            "schedule_n": self.schedule_n,
            "icon": self.icon,
            "reminder_time": self.reminder_time,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
