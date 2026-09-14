from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db
from .base import BaseModel, JSONType

CAPTURE_STATUSES = ("new", "processed", "discarded")
CAPTURE_TYPES = ("task", "event", "goal", "note", "tracker")


class Capture(BaseModel, db.Model):
    """Quick-inbox entry (plan 6.8). Raw text first, proposal after processing, result after confirm."""

    __tablename__ = "captures"

    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="new", index=True)
    parsed_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    # Full proposal: {"type", "fields", "confidence", "source", "reason"}
    parsed_json: Mapped[Optional[Any]] = mapped_column(JSONType, nullable=True)
    # "<type>:<uuid>" of the record created on confirm
    result_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict:
        from ..utils.dates import iso

        return {
            "id": str(self.id),
            "raw_text": self.raw_text,
            "status": self.status,
            "parsed_type": self.parsed_type,
            "proposal": self.parsed_json,
            "result_ref": self.result_ref,
            "processed_at": iso(self.processed_at),
            "created_at": iso(self.created_at),
            "updated_at": iso(self.updated_at),
        }
