import uuid
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db
from .base import BaseModel, JSONType


class Note(BaseModel, db.Model):
    __tablename__ = "notes"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    area_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("areas.id"), nullable=True, index=True)
    tags: Mapped[list] = mapped_column(JSONType, nullable=False, default=list)
    pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    def to_dict(self) -> dict:
        from ..utils.dates import iso

        return {
            "id": str(self.id),
            "title": self.title,
            "body": self.body,
            "area_id": str(self.area_id) if self.area_id else None,
            "tags": list(self.tags or []),
            "pinned": self.pinned,
            "created_at": iso(self.created_at),
            "updated_at": iso(self.updated_at),
        }
