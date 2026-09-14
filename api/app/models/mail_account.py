import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db
from .base import BaseModel


class MailAccount(BaseModel, db.Model):
    """One IMAP account (stream C). Passwords are never stored: `secret_ref` names
    the env entry (`env:<email>` in MAIL_ACCOUNTS_JSON) resolved at sync time."""

    __tablename__ = "mail_accounts"

    label: Mapped[str] = mapped_column(String(60), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    imap_host: Mapped[str] = mapped_column(String(255), nullable=False, default="imap.gmail.com")
    secret_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_uid: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    color: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def to_dict(self) -> dict:
        from ..utils.dates import iso

        return {
            "id": str(self.id),
            "label": self.label,
            "email": self.email,
            "imap_host": self.imap_host,
            "secret_ref": self.secret_ref,
            "last_uid": self.last_uid,
            "enabled": self.enabled,
            "color": self.color,
            "sort_order": self.sort_order,
            "last_synced_at": iso(self.last_synced_at),
            "last_error": self.last_error,
            "created_at": iso(self.created_at),
            "updated_at": iso(self.updated_at),
        }
