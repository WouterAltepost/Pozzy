"""Date helpers. Storage is UTC; the API layer converts using the timezone setting."""
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from ..settings_defaults import get_setting


def app_tz() -> ZoneInfo:
    """Timezone from Settings, cached on flask.g for the current request or app context.

    iso() calls this for every serialised datetime; without the cache a 200 row
    list issued 400 Settings queries (22 s against Supabase).
    """
    try:
        from flask import g, has_app_context

        if has_app_context():
            cached = getattr(g, "_pozzy_tz", None)
            if cached is not None:
                return cached
            tz = ZoneInfo(get_setting("timezone"))
            g._pozzy_tz = tz
            return tz
        return ZoneInfo(get_setting("timezone"))
    except Exception:
        return ZoneInfo("Europe/Amsterdam")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def today_local(now: datetime | None = None) -> date:
    return (now or now_utc()).astimezone(app_tz()).date()


def as_utc(value: datetime | None) -> datetime | None:
    """Normalise a datetime read from the DB. SQLite drops tzinfo; stored values are always UTC."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def iso(value: datetime | None) -> str | None:
    """Serialise a stored datetime as ISO 8601 in the app timezone."""
    if value is None:
        return None
    return as_utc(value).astimezone(app_tz()).isoformat()


def week_start_of(day: date) -> date:
    """Monday of the week containing `day`."""
    return day - timedelta(days=day.weekday())
