import uuid
from datetime import date
from typing import Optional

from sqlalchemy import Boolean, Date, Float, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db
from .base import BaseModel


class WeeklyGoal(BaseModel, db.Model):
    __tablename__ = "weekly_goals"

    week_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    area_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("areas.id"), nullable=True, index=True)
    target_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_value: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    done: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    @property
    def progress(self) -> float | None:
        if not self.target_value:
            return 1.0 if self.done else None
        return min(1.0, (self.current_value or 0) / self.target_value)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "week_start": self.week_start.isoformat(),
            "title": self.title,
            "area_id": str(self.area_id) if self.area_id else None,
            "target_value": self.target_value,
            "current_value": self.current_value,
            "progress": self.progress,
            "done": self.done,
            "notes": self.notes,
        }
