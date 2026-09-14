from datetime import date
from typing import Optional

from sqlalchemy import Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db
from .base import BaseModel

APPLICATION_STATUSES = ("found", "applied", "interview", "offer", "rejected")


class Application(BaseModel, db.Model):
    __tablename__ = "applications"

    company: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="found", index=True)
    applied_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    next_step: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    next_step_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "company": self.company,
            "role": self.role,
            "status": self.status,
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
            "next_step": self.next_step,
            "next_step_date": self.next_step_date.isoformat() if self.next_step_date else None,
            "notes": self.notes,
            "link": self.link,
        }
