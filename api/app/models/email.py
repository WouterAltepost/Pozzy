import uuid
from datetime import datetime
from typing import Optional
from urllib.parse import quote

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db
from .base import BaseModel, JSONType

EMAIL_CATEGORIES = ("client", "school", "finance", "personal", "newsletter", "notification", "other")
EMAIL_PRIORITIES = (1, 2, 3, 4)
DEFAULT_PRIORITY = 3
DEFAULT_CATEGORY = "other"


class Email(BaseModel, db.Model):
    """One INBOX message reduced to headers plus a snippet (stream C).

    Classification columns (priority, category, area_id, needs_reply, summary)
    are written by the classifier. Manual overrides live in separate
    `*_override` columns so re-classification never clobbers them.
    """

    __tablename__ = "emails"
    __table_args__ = (UniqueConstraint("account_id", "uid", name="uq_emails_account_uid"),)

    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("mail_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    uid: Mapped[int] = mapped_column(Integer, nullable=False)
    message_id: Mapped[Optional[str]] = mapped_column(String(998), nullable=True, index=True)
    thread_hint: Mapped[Optional[str]] = mapped_column(String(998), nullable=True)
    from_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    from_email: Mapped[str] = mapped_column(String(320), nullable=False, default="", index=True)
    to_addrs: Mapped[list] = mapped_column(JSONType, nullable=False, default=list)
    subject: Mapped[str] = mapped_column(Text, nullable=False, default="")
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    snippet: Mapped[str] = mapped_column(Text, nullable=False, default="")
    labels: Mapped[list] = mapped_column(JSONType, nullable=False, default=list)
    has_attachments: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    priority: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    category: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    area_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("areas.id"), nullable=True)
    needs_reply: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    classifier: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    classified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    priority_override: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    category_override: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    area_override_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("areas.id"), nullable=True)

    handled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    handled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    account = relationship("MailAccount", lazy="joined")

    @property
    def effective_priority(self) -> int:
        return self.priority_override or self.priority or DEFAULT_PRIORITY

    @property
    def effective_category(self) -> str:
        return self.category_override or self.category or DEFAULT_CATEGORY

    @property
    def effective_area_id(self):
        return self.area_override_id or self.area_id

    @property
    def gmail_url(self) -> Optional[str]:
        if not self.message_id or self.account is None:
            return None
        mid = self.message_id.strip("<>")
        return f"https://mail.google.com/mail/u/{quote(self.account.email)}/#search/rfc822msgid:{quote(mid, safe='')}"

    def to_dict(self, with_snippet: bool = False) -> dict:
        from ..utils.dates import iso

        out = {
            "id": str(self.id),
            "account_id": str(self.account_id),
            "account": None
            if self.account is None
            else {"id": str(self.account.id), "label": self.account.label, "email": self.account.email, "color": self.account.color},
            "uid": self.uid,
            "message_id": self.message_id,
            "from_name": self.from_name,
            "from_email": self.from_email,
            "to_addrs": list(self.to_addrs or []),
            "subject": self.subject,
            "date": iso(self.date),
            "labels": list(self.labels or []),
            "has_attachments": self.has_attachments,
            "priority": self.effective_priority,
            "category": self.effective_category,
            "area_id": str(self.effective_area_id) if self.effective_area_id else None,
            "needs_reply": self.needs_reply,
            "summary": self.summary,
            "classifier": self.classifier,
            "classified_at": iso(self.classified_at),
            "raw": {
                "priority": self.priority,
                "category": self.category,
                "area_id": str(self.area_id) if self.area_id else None,
            },
            "overrides": {
                "priority": self.priority_override,
                "category": self.category_override,
                "area_id": str(self.area_override_id) if self.area_override_id else None,
            },
            "handled": self.handled,
            "handled_at": iso(self.handled_at),
            "gmail_url": self.gmail_url,
            "created_at": iso(self.created_at),
        }
        if with_snippet:
            out["snippet"] = self.snippet
        return out
