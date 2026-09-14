from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import Date, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db
from .base import BaseModel, JSONType


class DailyBriefing(BaseModel, db.Model):
    """One briefing text per day (plan 6.1). `source` is claude or deterministic."""

    __tablename__ = "daily_briefings"

    date: Mapped[date] = mapped_column(Date, nullable=False, unique=True)
    text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="deterministic")
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # The context handed to the model, kept so a bad briefing can be explained.
    context_json: Mapped[Optional[Any]] = mapped_column(JSONType, nullable=True)
    generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict:
        from ..utils.dates import iso

        return {
            "id": str(self.id),
            "date": self.date.isoformat(),
            "text": self.text,
            "source": self.source,
            "model": self.model,
            "generated_at": iso(self.generated_at),
        }
