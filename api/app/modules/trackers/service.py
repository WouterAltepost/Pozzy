"""Trackers: habits per area, weekly grid, streaks, history for charts."""
from datetime import date, timedelta

from sqlalchemy import select

from ...extensions import db
from ...models import Area, Tracker, TrackerEntry
from ...utils.dates import today_local, week_start_of
from ...utils.validation import ValidationError, to_uuid

GRID_TYPES = ("daily_bool", "weekly_count")


def _check_area(area_id):
    if area_id is not None and db.session.get(Area, area_id) is None:
        raise ValidationError("'area_id' does not match an area")


def list_trackers(include_inactive: bool = False) -> list[Tracker]:
    stmt = select(Tracker)
    if not include_inactive:
        stmt = stmt.where(Tracker.active.is_(True))
    return db.session.scalars(stmt.order_by(Tracker.sort_order, Tracker.created_at)).all()


def get_tracker(tracker_id) -> Tracker | None:
    key = to_uuid(tracker_id)
    return db.session.get(Tracker, key) if key else None


def create_tracker(fields: dict) -> Tracker:
    _check_area(fields.get("area_id"))
    if fields.get("sort_order") is None:
        fields["sort_order"] = max((t.sort_order for t in list_trackers(True)), default=0) + 1
    if fields["type"] == "weekly_count":
        fields["target_period"] = "week"
    elif fields["type"] == "daily_bool":
        fields["target_period"] = "day"
        fields["target_value"] = 1
    tracker = Tracker(**fields)
    db.session.add(tracker)
    db.session.commit()
    return tracker


def update_tracker(tracker: Tracker, fields: dict) -> Tracker:
    if "area_id" in fields:
        _check_area(fields["area_id"])
    for key, value in fields.items():
        setattr(tracker, key, value)
    db.session.commit()
    return tracker


def delete_tracker(tracker: Tracker) -> None:
    db.session.delete(tracker)
    db.session.commit()


def upsert_entry(tracker: Tracker, day: date, value: float, note: str | None = None) -> TrackerEntry:
    entry = db.session.scalar(select(TrackerEntry).where(TrackerEntry.tracker_id == tracker.id, TrackerEntry.date == day))
    if entry is None:
        entry = TrackerEntry(tracker_id=tracker.id, date=day, value=value, note=note)
        db.session.add(entry)
    else:
        entry.value = value
        if note is not None:
            entry.note = note
    db.session.commit()
    return entry


def delete_entry(tracker: Tracker, day: date) -> bool:
    entry = db.session.scalar(select(TrackerEntry).where(TrackerEntry.tracker_id == tracker.id, TrackerEntry.date == day))
    if entry is None:
        return False
    db.session.delete(entry)
    db.session.commit()
    return True


def tick(tracker: Tracker, day: date) -> TrackerEntry:
    """Quick action: bool toggles 1/0, count increments by 1, numeric/duration add the target or 1."""
    entry = db.session.scalar(select(TrackerEntry).where(TrackerEntry.tracker_id == tracker.id, TrackerEntry.date == day))
    current = entry.value if entry else 0
    if tracker.type == "daily_bool":
        value = 0 if current else 1
    elif tracker.type == "weekly_count":
        value = current + 1
    else:
        value = current + (tracker.target_value if tracker.target_period == "day" and tracker.target_value else 1)
    return upsert_entry(tracker, day, value)


def entries_between(tracker_ids, start: date, end: date) -> dict:
    stmt = select(TrackerEntry).where(TrackerEntry.tracker_id.in_(list(tracker_ids)), TrackerEntry.date >= start, TrackerEntry.date <= end)
    out: dict = {}
    for e in db.session.scalars(stmt).all():
        out.setdefault(e.tracker_id, {})[e.date] = e
    return out


def _met(tracker: Tracker, value: float) -> bool:
    if tracker.type == "daily_bool":
        return value > 0
    if tracker.target_value is None:
        return value > 0
    return value >= tracker.target_value


def streak(tracker: Tracker, entries_by_date: dict, today: date) -> int:
    """Consecutive days (day targets) or weeks (week targets) met, ending today or the last period."""
    if tracker.target_period == "day":
        count, day = 0, today
        # Today not yet met does not break the streak.
        if not _met(tracker, entries_by_date.get(day).value if entries_by_date.get(day) else 0):
            day -= timedelta(days=1)
        while True:
            entry = entries_by_date.get(day)
            if entry is None or not _met(tracker, entry.value):
                return count
            count += 1
            day -= timedelta(days=1)
    week = week_start_of(today)
    count = 0
    if not _met(tracker, _week_sum(entries_by_date, week)):
        week -= timedelta(days=7)
    while _met(tracker, _week_sum(entries_by_date, week)):
        count += 1
        week -= timedelta(days=7)
        if count > 520:
            break
    return count


def _week_sum(entries_by_date: dict, week: date) -> float:
    return sum(e.value for d, e in entries_by_date.items() if week <= d < week + timedelta(days=7))


def week_grid(week_start: date | None = None, include_inactive: bool = False) -> dict:
    today = today_local()
    start = week_start or week_start_of(today)
    end = start + timedelta(days=6)
    trackers = list_trackers(include_inactive)
    # 1 year of history for streaks, fetched once.
    history = entries_between([t.id for t in trackers], start - timedelta(days=366), max(end, today))
    areas = {a.id: a for a in db.session.scalars(select(Area)).all()}
    rows = []
    for t in trackers:
        by_date = history.get(t.id, {})
        days = []
        for i in range(7):
            d = start + timedelta(days=i)
            e = by_date.get(d)
            days.append({"date": d.isoformat(), "value": e.value if e else None, "note": e.note if e else None, "met": _met(t, e.value) if e else False})
        week_total = sum(d["value"] or 0 for d in days)
        if t.target_period == "week":
            completion = min(1.0, week_total / t.target_value) if t.target_value else (1.0 if week_total > 0 else 0.0)
        else:
            elapsed = 7 if end < today else max(1, min(7, (today - start).days + 1))
            completion = sum(1 for d in days[:elapsed] if d["met"]) / elapsed
        area = areas.get(t.area_id)
        rows.append(
            {
                **t.to_dict(),
                "area_name": area.name if area else None,
                "area_color": area.color if area else None,
                "days": days,
                "week_total": week_total,
                "completion": round(completion, 3),
                "streak": streak(t, by_date, today),
            }
        )
    return {"week_start": start.isoformat(), "week_end": end.isoformat(), "today": today.isoformat(), "trackers": rows}


def history(tracker: Tracker, weeks: int = 8) -> dict:
    today = today_local()
    start = week_start_of(today) - timedelta(days=7 * (weeks - 1))
    by_date = entries_between([tracker.id], start, today).get(tracker.id, {})
    points = [{"date": d.isoformat(), "value": e.value, "note": e.note} for d, e in sorted(by_date.items())]
    weekly = []
    for i in range(weeks):
        ws = start + timedelta(days=7 * i)
        vals = [e.value for d, e in by_date.items() if ws <= d < ws + timedelta(days=7)]
        weekly.append({"week_start": ws.isoformat(), "sum": sum(vals), "avg": (sum(vals) / len(vals)) if vals else None, "count": len(vals)})
    return {"tracker": tracker.to_dict(), "from": start.isoformat(), "to": today.isoformat(), "points": points, "weekly": weekly}
