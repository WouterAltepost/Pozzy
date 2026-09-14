from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db
from .base import BaseModel


class JobRun(BaseModel, db.Model):
    __tablename__ = "job_runs"

    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ok: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
