"""Pydantic shapes for capture proposals.

The same models validate Claude's answer (claude_client.parse_capture) and the
fields Wouter sends back on confirm, so both paths are checked the same way.
"""
from datetime import date as DateType, datetime as DateTimeType
from typing import Literal

from pydantic import BaseModel, Field, field_validator

CaptureType = Literal["task", "event", "goal", "note", "tracker"]


def _clean_str(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None


class TaskFields(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    area: str | None = None
    tags: list[str] = []
    urgent: bool = False
    important: bool = False
    due_date: DateType | None = None
    estimated_minutes: int | None = Field(default=None, ge=1, le=24 * 60)

    @field_validator("description", "area", mode="before")
    @classmethod
    def _strip(cls, v):
        return _clean_str(v)

    @field_validator("tags", mode="before")
    @classmethod
    def _tags(cls, v):
        if not v:
            return []
        return [str(t).strip().lstrip("#") for t in v if str(t).strip()][:20]


class EventFields(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    start: DateTimeType
    end: DateTimeType | None = None
    area: str | None = None
    description: str | None = None

    @field_validator("description", "area", mode="before")
    @classmethod
    def _strip(cls, v):
        return _clean_str(v)


class GoalFields(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    area: str | None = None
    target_value: float | None = Field(default=None, ge=0)
    week: Literal["this", "next"] = "this"

    @field_validator("area", mode="before")
    @classmethod
    def _strip(cls, v):
        return _clean_str(v)


class NoteFields(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = ""
    area: str | None = None
    tags: list[str] = []

    @field_validator("area", mode="before")
    @classmethod
    def _strip(cls, v):
        return _clean_str(v)

    @field_validator("tags", mode="before")
    @classmethod
    def _tags(cls, v):
        if not v:
            return []
        return [str(t).strip().lstrip("#") for t in v if str(t).strip()][:20]


class TrackerFields(BaseModel):
    tracker: str = Field(min_length=1, max_length=100)
    date: DateType | None = None
    value: float = 1
    note: str | None = None

    @field_validator("note", mode="before")
    @classmethod
    def _strip(cls, v):
        return _clean_str(v)


FIELD_MODELS: dict[str, type[BaseModel]] = {
    "task": TaskFields,
    "event": EventFields,
    "goal": GoalFields,
    "note": NoteFields,
    "tracker": TrackerFields,
}


class CaptureProposal(BaseModel):
    """What Claude returns. `fields` is validated against the model for `type` in `validate_fields`."""

    type: CaptureType
    confidence: float = Field(default=0.5, ge=0, le=1)
    reason: str = ""
    fields: dict


def validate_fields(kind: str, fields: dict) -> dict:
    """Return JSON-safe validated fields for `kind`. Raises pydantic.ValidationError."""
    model = FIELD_MODELS[kind]
    return model.model_validate(fields or {}).model_dump(mode="json")
