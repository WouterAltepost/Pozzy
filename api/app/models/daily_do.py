import uuid
from datetime import date
from typing import Optional

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db
from .base import BaseModel


class DailyDo(BaseModel, db.Model):
    __tablename__ = "daily_dos"

    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    task_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    done: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Date the do was first created; set only on rolled copies. Roll count = date - rolled_from_date.
    rolled_from_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    @property
    def roll_count(self) -> int:
        if not self.rolled_from_date:
            return 0
        return max(0, (self.date - self.rolled_from_date).days)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "date": self.date.isoformat(),
            "task_id": str(self.task_id) if self.task_id else None,
            "title": self.title,
            "done": self.done,
            "rolled_from_date": self.rolled_from_date.isoformat() if self.rolled_from_date else None,
            "roll_count": self.roll_count,
            "warning": self.roll_count >= 2,
            "position": self.position,
        }
