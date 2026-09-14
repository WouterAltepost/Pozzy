import uuid
from typing import Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db
from .base import BaseModel

TRACKER_TYPES = ("daily_bool", "weekly_count", "numeric", "duration")
TARGET_PERIODS = ("day", "week")


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
        }
