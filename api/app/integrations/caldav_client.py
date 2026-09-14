"""iCloud CalDAV client (stream B).

Two layers:

1. Pure functions with no network: `parse_occurrences` expands one ICS blob
   (a VCALENDAR with one or more VEVENT components sharing a UID) into concrete
   occurrences inside a window, and `build_ics` produces the VCALENDAR text we
   write back. Both are unit tested with recorded fixtures.

2. `CalDAVClient`, a thin wrapper around `caldav.DAVClient` that lists calendars,
   fetches raw events with their etags, and creates, updates and deletes events
   by UID. Every network call retries on 5xx with backoff. The sync job decides
   what to do with failures; this module never swallows them silently.

Recurrence expansion is done locally with `recurring-ical-events` (server side
expansion on iCloud is unreliable and drops modified occurrences). Fetching
with expand=False returns the master VEVENT plus any RECURRENCE-ID overrides
in the same blob, which is exactly what the expander needs.

All datetimes returned by `parse_occurrences` are timezone aware UTC.
"""
from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import caldav
import recurring_ical_events
from caldav.elements import dav
from caldav.lib import error as caldav_error
from icalendar import Calendar as ICalendar
from icalendar import Event as IEvent

log = logging.getLogger(__name__)

TASK_ID_PROP = "X-POZZY-TASK-ID"
PRODID = "-//Pozzy//Pozzy Agenda//EN"
DEFAULT_TZ = "Europe/Amsterdam"
RETRY_DELAYS = (1.0, 3.0)  # seconds between attempts; 3 attempts total


class CalDAVError(Exception):
    """Raised when a CalDAV call fails after retries."""


@dataclass(frozen=True)
class Occurrence:
    uid: str
    recurrence_id: str | None  # ISO string of the original occurrence start, None for single events
    title: str
    start: datetime  # UTC
    end: datetime  # UTC, exclusive
    all_day: bool
    location: str | None
    description: str | None
    task_id: str | None


@dataclass(frozen=True)
class RawEvent:
    href: str
    etag: str | None
    ics: str


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def _to_utc(value: datetime | date, tz: ZoneInfo) -> datetime:
    """Normalise a DTSTART/DTEND value to aware UTC.

    Dates (all-day) become local midnight in `tz`. Floating datetimes (no tzinfo)
    are interpreted in `tz`. Aware datetimes are converted.
    """
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=tz)
        return value.astimezone(timezone.utc)
    return datetime(value.year, value.month, value.day, tzinfo=tz).astimezone(timezone.utc)


def _text(component: IEvent, name: str) -> str | None:
    raw = component.get(name)
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def _recurrence_key(component: IEvent) -> str | None:
    rid = component.get("RECURRENCE-ID")
    if rid is None:
        return None
    value = rid.dt
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.isoformat()
        return value.astimezone(timezone.utc).isoformat()
    return value.isoformat()


def parse_occurrences(
    ics_text: str,
    window_start: datetime,
    window_end: datetime,
    default_tz: str = DEFAULT_TZ,
) -> list[Occurrence]:
    """Expand one calendar object into concrete occurrences overlapping the window.

    `window_start` and `window_end` must be aware datetimes. Single events yield
    one Occurrence with recurrence_id None. Recurring events yield one per
    occurrence with recurrence_id set to the original occurrence start (UTC ISO
    string), so an occurrence moved by an override keeps a stable key.
    """
    tz = ZoneInfo(default_tz)
    cal = ICalendar.from_ical(ics_text)
    # The expander stamps RECURRENCE-ID on every occurrence, single events
    # included, so decide "recurring" from the source components instead.
    recurring_uids: set[str] = set()
    for source in cal.walk("VEVENT"):
        source_uid = _text(source, "UID")
        if source_uid and any(source.get(k) is not None for k in ("RRULE", "RDATE", "RECURRENCE-ID")):
            recurring_uids.add(source_uid)

    query = recurring_ical_events.of(cal, keep_recurrence_attributes=True, skip_bad_series=False)
    out: list[Occurrence] = []
    for component in query.between(window_start, window_end):
        uid = _text(component, "UID")
        if not uid:
            continue
        dtstart = component.get("DTSTART").dt
        all_day = not isinstance(dtstart, datetime)
        dtend_prop = component.get("DTEND")
        if dtend_prop is not None:
            dtend = dtend_prop.dt
        else:
            duration = component.get("DURATION")
            if duration is not None:
                dtend = dtstart + duration.dt
            elif all_day:
                dtend = dtstart + timedelta(days=1)
            else:
                dtend = dtstart
        start = _to_utc(dtstart, tz)
        end = _to_utc(dtend, tz)
        if end <= start:
            end = start + (timedelta(days=1) if all_day else timedelta(0))

        recurrence_id = _recurrence_key(component) if uid in recurring_uids else None

        out.append(
            Occurrence(
                uid=uid,
                recurrence_id=recurrence_id,
                title=_text(component, "SUMMARY") or "(no title)",
                start=start,
                end=end,
                all_day=all_day,
                location=_text(component, "LOCATION"),
                description=_text(component, "DESCRIPTION"),
                task_id=_text(component, TASK_ID_PROP),
            )
        )
    out.sort(key=lambda o: (o.start, o.title))
    return out


def build_ics(
    *,
    title: str,
    start: datetime,
    end: datetime,
    all_day: bool = False,
    location: str | None = None,
    description: str | None = None,
    task_id: str | None = None,
    uid: str | None = None,
    tz: str = DEFAULT_TZ,
) -> tuple[str, str]:
    """Return (uid, ics_text) for a single non-recurring VEVENT.

    Timed events are written in UTC (Z suffix), which every CalDAV server and the
    iPhone display correctly in local time. All-day events are written as DATE
    values in the local calendar day of `tz`.
    """
    uid = uid or str(uuid.uuid4())
    zone = ZoneInfo(tz)
    cal = ICalendar()
    cal.add("PRODID", PRODID)
    cal.add("VERSION", "2.0")
    ev = IEvent()
    ev.add("UID", uid)
    ev.add("DTSTAMP", datetime.now(timezone.utc))
    ev.add("SUMMARY", title)
    if all_day:
        ev.add("DTSTART", start.astimezone(zone).date())
        ev.add("DTEND", end.astimezone(zone).date())
    else:
        ev.add("DTSTART", start.astimezone(timezone.utc))
        ev.add("DTEND", end.astimezone(timezone.utc))
    if location:
        ev.add("LOCATION", location)
    if description:
        ev.add("DESCRIPTION", description)
    if task_id:
        ev.add(TASK_ID_PROP, str(task_id))
    cal.add_component(ev)
    return uid, cal.to_ical().decode("utf-8")


# ---------------------------------------------------------------------------
# Network client
# ---------------------------------------------------------------------------


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, caldav_error.AuthorizationError):
        return False
    if isinstance(exc, caldav_error.NotFoundError):
        return False
    if isinstance(exc, caldav_error.DAVError):
        return True  # iCloud 5xx surface as generic DAVError subclasses
    import requests

    return isinstance(exc, (requests.ConnectionError, requests.Timeout))


def _with_retry(label: str, fn):
    attempts = len(RETRY_DELAYS) + 1
    for attempt in range(attempts):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            if attempt == attempts - 1 or not _is_retryable(exc):
                raise CalDAVError(f"{label}: {exc.__class__.__name__}: {exc}") from exc
            delay = RETRY_DELAYS[attempt]
            log.warning("CalDAV %s failed (%s), retry in %.0fs", label, exc.__class__.__name__, delay)
            time.sleep(delay)
    raise AssertionError("unreachable")


class CalDAVClient:
    def __init__(self, url: str, username: str, password: str, timeout: int = 30):
        self._client = caldav.DAVClient(url=url, username=username, password=password, timeout=timeout)
        self._principal = None

    # -- discovery ----------------------------------------------------------

    def _get_principal(self):
        if self._principal is None:
            self._principal = _with_retry("principal", self._client.principal)
        return self._principal

    def list_calendars(self) -> list[dict]:
        """Return [{name, url}] for every calendar the principal can see."""

        def go():
            return [
                {"name": str(cal.name or cal.url), "url": str(cal.url)}
                for cal in self._get_principal().calendars()
            ]

        return _with_retry("list_calendars", go)

    def _ensure_home(self):
        """Resolve the calendar home once. iCloud redirects from caldav.icloud.com to a
        pNN-caldav host; caldav.DAVClient only updates its base URL during that lookup, and
        without it any request for a stored pNN calendar URL fails with "can't be joined"."""
        if not getattr(self, "_home_resolved", False):
            principal = self._get_principal()
            _with_retry("calendar_home", lambda: principal.calendar_home_set)
            self._home_resolved = True

    def _calendar(self, calendar_url: str):
        self._ensure_home()
        return self._client.calendar(url=calendar_url)

    # -- read ---------------------------------------------------------------

    def fetch_events(self, calendar_url: str, start: datetime, end: datetime) -> list[RawEvent]:
        """Raw VEVENT objects overlapping [start, end), unexpanded, with etags."""

        def go():
            cal = self._calendar(calendar_url)
            objs = cal.search(start=start, end=end, event=True, expand=False, props=[dav.GetEtag()])
            out = []
            for obj in objs:
                props = getattr(obj, "props", None) or {}
                etag = props.get(dav.GetEtag.tag)
                out.append(RawEvent(href=str(obj.url), etag=str(etag).strip() if etag else None, ics=obj.data))
            return out

        return _with_retry("fetch_events", go)

    def get_event(self, calendar_url: str, uid: str) -> RawEvent | None:
        def go():
            cal = self._calendar(calendar_url)
            try:
                obj = cal.event_by_uid(uid)
            except caldav_error.NotFoundError:
                return None
            obj.load()
            return RawEvent(href=str(obj.url), etag=None, ics=obj.data)

        return _with_retry("get_event", go)

    # -- write --------------------------------------------------------------

    def create_event(self, calendar_url: str, ics_text: str) -> str:
        """PUT a new object. Returns its href."""

        def go():
            cal = self._calendar(calendar_url)
            obj = cal.save_event(ical=ics_text)
            return str(obj.url)

        return _with_retry("create_event", go)

    def update_event(self, calendar_url: str, uid: str, ics_text: str) -> str:
        """Overwrite the object with this UID. Returns its href."""

        def go():
            cal = self._calendar(calendar_url)
            obj = cal.event_by_uid(uid)
            obj.data = ics_text
            obj.save()
            return str(obj.url)

        return _with_retry("update_event", go)

    def delete_event(self, calendar_url: str, uid: str) -> bool:
        """Delete by UID. Returns False if it was already gone."""

        def go():
            cal = self._calendar(calendar_url)
            try:
                obj = cal.event_by_uid(uid)
            except caldav_error.NotFoundError:
                return False
            obj.delete()
            return True

        return _with_retry("delete_event", go)


def client_from_config(config) -> CalDAVClient:
    """Build a client from Flask config (ICLOUD_USERNAME, ICLOUD_APP_PASSWORD, ICLOUD_CALDAV_URL)."""
    username = config.get("ICLOUD_USERNAME")
    password = config.get("ICLOUD_APP_PASSWORD")
    if not username or not password:
        raise CalDAVError("ICLOUD_USERNAME and ICLOUD_APP_PASSWORD are not set")
    url = config.get("ICLOUD_CALDAV_URL") or "https://caldav.icloud.com"
    return CalDAVClient(url=url, username=username, password=password)
