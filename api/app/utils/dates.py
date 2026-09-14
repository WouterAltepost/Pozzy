"""Date helpers. Storage is UTC; the API layer converts using the timezone setting."""
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from ..settings_defaults import get_setting


def app_tz() -> ZoneInfo:
    try:
        return ZoneInfo(get_setting("timezone"))
    except Exception:
        return ZoneInfo("Europe/Amsterdam")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def today_local(now: datetime | None = None) -> date:
    return (now or now_utc()).astimezone(app_tz()).date()


def iso(value: datetime | None) -> str | None:
    """Serialise a stored datetime as ISO 8601 in the app timezone."""
    if value is None:
        return None
    if value.tzinfo is None:  # SQLite drops tzinfo; stored values are always UTC
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(app_tz()).isoformat()


def week_start_of(day: date) -> date:
    """Monday of the week containing `day`."""
    return day - timedelta(days=day.weekday())
