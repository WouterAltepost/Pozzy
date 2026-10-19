from typing import Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db
from .base import BaseModel


class PushSubscription(BaseModel, db.Model):
    """A browser's Web Push subscription (one per installed PWA or browser profile)."""

    __tablename__ = "push_subscriptions"

    endpoint: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    p256dh: Mapped[str] = mapped_column(String(200), nullable=False)
    auth: Mapped[str] = mapped_column(String(100), nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)

    def to_dict(self) -> dict:
        return {"id": str(self.id), "endpoint": self.endpoint, "user_agent": self.user_agent, "created_at": self.created_at.isoformat() if self.created_at else None}
