"""Deterministic free-slot engine. Pure function, no DB, no Claude.

Working window and events are compared in the app timezone so a slot never
straddles a DST change incorrectly: each working day is built from local wall
clock times and converted to aware datetimes via zoneinfo.

`window` shape (from Settings `working_window`, plus optional `timezone`):
    {"days": [1, 2, 3, 4, 5], "start": "08:00", "end": "18:00", "timezone": "Europe/Amsterdam"}
`days` uses ISO weekday numbers (1 = Monday, 7 = Sunday).

Returns [{start, end, day_label, reason_hints}] with `start`/`end` as aware
datetimes in the app timezone. Slots are aligned to `step_min` and never
start in the past relative to `from_dt`.
"""
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

DEFAULT_WINDOW = {"days": [1, 2, 3, 4, 5], "start": "08:00", "end": "18:00", "timezone": "Europe/Amsterdam"}

Interval = tuple[datetime, datetime]


def _parse_hhmm(value: str) -> time:
    hours, minutes = value.split(":")
    return time(int(hours), int(minutes))


def _merge(intervals: list[Interval]) -> list[Interval]:
    """Sort and merge overlapping or touching busy intervals."""
    ordered = sorted((s, e) for s, e in intervals if e > s)
    merged: list[Interval] = []
    for start, end in ordered:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def _ceil_to_step(dt: datetime, step_min: int) -> datetime:
    remainder = (dt.minute % step_min, dt.second, dt.microsecond)
    if remainder == (0, 0, 0):
        return dt
    floored = dt.replace(second=0, microsecond=0, minute=dt.minute - dt.minute % step_min)
    return floored + timedelta(minutes=step_min)


def find_free_slots(
    events: list[Interval],
    scheduled_tasks: list[Interval],
    window: dict,
    duration_min: int,
    from_dt: datetime,
    days: int = 7,
    step_min: int = 15,
    max_per_gap: int | None = None,
) -> list[dict]:
    if duration_min <= 0:
        raise ValueError("duration_min must be positive")
    if from_dt.tzinfo is None:
        raise ValueError("from_dt must be timezone aware")

    cfg = {**DEFAULT_WINDOW, **(window or {})}
    tz = ZoneInfo(cfg.get("timezone") or "Europe/Amsterdam")
    work_days = set(int(d) for d in cfg["days"])
    day_start = _parse_hhmm(cfg["start"])
    day_end = _parse_hhmm(cfg["end"])
    duration = timedelta(minutes=duration_min)

    busy = _merge([(s.astimezone(tz), e.astimezone(tz)) for s, e in list(events) + list(scheduled_tasks)])

    now_local = from_dt.astimezone(tz)
    first_day = now_local.date()
    slots: list[dict] = []

    for offset in range(days):
        day = first_day + timedelta(days=offset)
        if day.isoweekday() not in work_days:
            continue
        # Build local wall-clock bounds for this day. zoneinfo handles DST for the day itself.
        window_start = datetime.combine(day, day_start, tzinfo=tz)
        window_end = datetime.combine(day, day_end, tzinfo=tz)
        if window_end <= window_start:
            continue
        cursor = max(window_start, _ceil_to_step(now_local, step_min))
        if cursor >= window_end:
            continue

        day_busy = [(max(s, window_start), min(e, window_end)) for s, e in busy if e > window_start and s < window_end]
        gaps: list[Interval] = []
        for b_start, b_end in day_busy:
            if b_start > cursor:
                gaps.append((cursor, b_start))
            cursor = max(cursor, b_end)
        if cursor < window_end:
            gaps.append((cursor, window_end))

        for gap_start, gap_end in gaps:
            gap_start = _ceil_to_step(gap_start, step_min)
            produced = 0
            start = gap_start
            while start + duration <= gap_end:
                end = start + duration
                slots.append(
                    {
                        "start": start,
                        "end": end,
                        "day_label": start.strftime("%a %d %b"),
                        "reason_hints": _hints(start, end, gap_start, gap_end, offset, day_busy),
                    }
                )
                produced += 1
                if max_per_gap and produced >= max_per_gap:
                    break
                start = end
    return slots


def _hints(start, end, gap_start, gap_end, day_offset, day_busy) -> list[str]:
    hints = []
    if start.hour < 12:
        hints.append("morning")
    elif start.hour < 14:
        hints.append("midday")
    else:
        hints.append("afternoon")
    if day_offset == 0:
        hints.append("today")
    elif day_offset == 1:
        hints.append("tomorrow")
    if start == gap_start:
        hints.append("gap_start")
    if end == gap_end:
        hints.append("gap_end")
    gap_minutes = int((gap_end - gap_start).total_seconds() // 60)
    if gap_minutes >= 180:
        hints.append("long_gap")
    if not day_busy:
        hints.append("empty_day")
    return hints


def rank_slots_deterministic(slots: list[dict], due_date=None, limit: int = 3, spread: bool = True) -> list[dict]:
    """Fallback ranking used until stream D adds Claude ranking.

    Prefers slots before the due date, then earlier days, then mornings, then
    slots that start at the beginning of a gap. With `spread`, at most one slot
    per day is returned so the top 3 are not three consecutive quarter hours.
    """

    def key(slot):
        start = slot["start"]
        after_due = 1 if (due_date and start.date() > due_date) else 0
        morning = 0 if start.hour < 12 else 1
        gap_start = 0 if "gap_start" in slot["reason_hints"] else 1
        return (after_due, start.date(), morning, gap_start, start)

    ordered = sorted(slots, key=key)
    if not spread:
        return ordered[:limit]
    picked, seen_days = [], set()
    for slot in ordered:
        day = slot["start"].date()
        if day in seen_days:
            continue
        seen_days.add(day)
        picked.append(slot)
        if len(picked) >= limit:
            break
    if len(picked) < limit:
        for slot in ordered:
            if slot not in picked:
                picked.append(slot)
            if len(picked) >= limit:
                break
    return picked


def slot_to_dict(slot: dict) -> dict:
    return {
        "start": slot["start"].isoformat(),
        "end": slot["end"].isoformat(),
        "day_label": slot["day_label"],
        "reason_hints": list(slot["reason_hints"]),
    }
