import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db
from .base import BaseModel

DEADLINE_TYPES = ("assignment", "exam", "presentation", "other")


class Deadline(BaseModel, db.Model):
    __tablename__ = "deadlines"

    course_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="assignment")
    done: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    task_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)

    course = relationship("Course", back_populates="deadlines")

    def to_dict(self) -> dict:
        from ..utils.dates import iso

        return {
            "id": str(self.id),
            "course_id": str(self.course_id),
            "course_name": self.course.name if self.course else None,
            "course_code": self.course.code if self.course else None,
            "title": self.title,
            "due_at": iso(self.due_at),
            "type": self.type,
            "done": self.done,
            "task_id": str(self.task_id) if self.task_id else None,
        }
