from typing import Optional

from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db
from .base import BaseModel

COURSE_STATUSES = ("active", "planned", "passed", "failed", "dropped")


class Course(BaseModel, db.Model):
    __tablename__ = "courses"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    period: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ects: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    deadlines = relationship("Deadline", back_populates="course", cascade="all, delete-orphan", order_by="Deadline.due_at")

    def to_dict(self, with_deadlines: bool = False) -> dict:
        out = {
            "id": str(self.id),
            "name": self.name,
            "code": self.code,
            "period": self.period,
            "ects": self.ects,
            "status": self.status,
        }
        if with_deadlines:
            out["deadlines"] = [d.to_dict() for d in self.deadlines]
        return out
