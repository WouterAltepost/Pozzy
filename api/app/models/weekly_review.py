from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import Boolean, Date, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db
from .base import BaseModel, JSONType


class WeeklyReview(BaseModel, db.Model):
    """Plan 6.11. One row per week (Monday). Stats are computed, reflection is Claude's, notes are Wouter's."""

    __tablename__ = "weekly_reviews"

    week_start: Mapped[date] = mapped_column(Date, nullable=False, unique=True)
    stats_json: Mapped[Optional[Any]] = mapped_column(JSONType, nullable=True)
    reflection: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reflection_source: Mapped[str] = mapped_column(String(20), nullable=False, default="none")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Draft goals for next week: [{"title", "area", "target_value", "reason"}]
    next_week_focus: Mapped[Optional[Any]] = mapped_column(JSONType, nullable=True)
    finalized: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    finalized_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict:
        from ..utils.dates import iso

        return {
            "id": str(self.id),
            "week_start": self.week_start.isoformat(),
            "stats": self.stats_json,
            "reflection": self.reflection,
            "reflection_source": self.reflection_source,
            "notes": self.notes,
            "next_week_focus": self.next_week_focus or [],
            "finalized": self.finalized,
            "finalized_at": iso(self.finalized_at),
            "generated_at": iso(self.generated_at),
            "created_at": iso(self.created_at),
            "updated_at": iso(self.updated_at),
        }
