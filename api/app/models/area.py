from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db
from .base import BaseModel


class Area(BaseModel, db.Model):
    __tablename__ = "areas"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def to_dict(self) -> dict:
        return {"id": str(self.id), "name": self.name, "color": self.color, "sort_order": self.sort_order}
