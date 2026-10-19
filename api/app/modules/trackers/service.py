"""Habits (trackers): schedules, the weekly grid, streaks, skips, stats and history for charts.

A day-period habit is due on the days its schedule names. A week-period habit (weekly_count,
or a target per week) is open all week and judged on the week total. Streaks only look at
days a habit was due: a day off in the schedule or a skipped day passes without breaking it,
and today not done yet never breaks it.
"""
from datetime import date, timedelta

from sqlalchemy import func, select

from ...extensions import db
from ...models import Area, Tracker, TrackerEntry
from ...models.tracker import ALL_DAYS
from ...utils.dates import today_local, week_start_of
from ...utils.validation import ValidationError, to_uuid

GRID_TYPES = ("daily_bool", "weekly_count")


def _check_area(area_id):
    if area_id is not None and db.session.get(Area, area_id) is None:
        raise ValidationError("'area_id' does not match an area")


def _normalise_schedule(fields: dict, tracker: Tracker | None = None) -> None:
    schedule = fields.get("schedule", tracker.schedule if tracker else "daily") or "daily"
    if schedule == "weekdays":
        days = fields.get("schedule_days", tracker.schedule_days if tracker else None)
        if not days or not (0 < days <= ALL_DAYS):
            raise ValidationError("'schedule_days' needs at least one weekday")
        fields["schedule_n"] = None
    elif schedule == "every_n_days":
        n = fields.get("schedule_n", tracker.schedule_n if tracker else None)
        if not n or n < 2:
            raise ValidationError("'schedule_n' must be 2 or more")
        fields["schedule_days"] = None
    else:
        fields["schedule_days"] = None
        fields["schedule_n"] = None
    fields["schedule"] = schedule


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
    _normalise_schedule(fields)
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
    if {"schedule", "schedule_days", "schedule_n"} & fields.keys():
        _normalise_schedule(fields, tracker)
    if "reminder_time" in fields:
        tracker.last_reminded_on = None
    kind = fields.get("type", tracker.type)
    if kind == "weekly_count":
        fields["target_period"] = "week"
    elif kind == "daily_bool":
        fields["target_period"] = "day"
        fields["target_value"] = 1
    for key, value in fields.items():
        setattr(tracker, key, value)
    db.session.commit()
    return tracker


def reorder(ids: list) -> list[Tracker]:
    """Set sort_order from the given id order; trackers not named keep their place after them."""
    keys = [to_uuid(i) for i in ids]
    if any(k is None for k in keys):
        raise ValidationError("'ids' must be tracker ids")
    by_id = {t.id: t for t in list_trackers(True)}
    ordered = [by_id[k] for k in keys if k in by_id] + [t for k, t in by_id.items() if k not in keys]
    for i, t in enumerate(ordered, start=1):
        t.sort_order = i
    db.session.commit()
    return ordered


def delete_tracker(tracker: Tracker) -> None:
    db.session.delete(tracker)
    db.session.commit()


def _entry(tracker: Tracker, day: date) -> TrackerEntry | None:
    return db.session.scalar(select(TrackerEntry).where(TrackerEntry.tracker_id == tracker.id, TrackerEntry.date == day))


def upsert_entry(tracker: Tracker, day: date, value: float, note: str | None = None, status: str = "done") -> TrackerEntry:
    """Write a day's value. A skip stores value 0; a note given as "" clears the note."""
    if status == "skipped":
        value = 0
    entry = _entry(tracker, day)
    if entry is None:
        entry = TrackerEntry(tracker_id=tracker.id, date=day, value=value, note=note or None, status=status)
        db.session.add(entry)
    else:
        entry.value = value
        entry.status = status
        if note is not None:
            entry.note = note or None
    db.session.commit()
    return entry


def delete_entry(tracker: Tracker, day: date) -> bool:
    entry = _entry(tracker, day)
    if entry is None:
        return False
    db.session.delete(entry)
    db.session.commit()
    return True


def _step(tracker: Tracker) -> float:
    """How much one tap adds: 1 for counts, the daily target (or 1) for numeric and duration."""
    if tracker.type == "weekly_count":
        return 1
    return tracker.target_value if tracker.target_period == "day" and tracker.target_value else 1


def tick(tracker: Tracker, day: date) -> TrackerEntry:
    """Quick action: bool toggles 1/0, count increments by 1, numeric/duration add the target or 1.
    A tap on a skipped day turns it into a done day."""
    entry = _entry(tracker, day)
    current = entry.value if entry and not entry.skipped else 0
    if tracker.type == "daily_bool":
        value = 0 if current else 1
    else:
        value = current + _step(tracker)
    return upsert_entry(tracker, day, value)


def untick(tracker: Tracker, day: date) -> TrackerEntry | None:
    """Reverse of tick: bool toggles back, the others subtract one step. Reaching zero removes
    the entry so the cell reads as untouched instead of showing a 0. Returns None when the
    entry is gone. A skipped day is un-skipped."""
    entry = _entry(tracker, day)
    if entry is None:
        return None
    if entry.skipped:
        delete_entry(tracker, day)
        return None
    if tracker.type == "daily_bool":
        value = 0 if entry.value else 1
    else:
        value = max(0, entry.value - _step(tracker))
    if tracker.type != "daily_bool" and value <= 0:
        delete_entry(tracker, day)
        return None
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


def _day_met(tracker: Tracker, entry: TrackerEntry | None) -> bool:
    """Met for one day of a day-period habit (a week-period habit's day counts when it has a value)."""
    if entry is None or entry.skipped:
        return False
    if tracker.target_period == "week":
        return entry.value > 0
    return _met(tracker, entry.value)


def is_weekly(tracker: Tracker) -> bool:
    return tracker.target_period == "week"


def is_due(tracker: Tracker, day: date, by_date: dict) -> bool:
    """Whether a day-period habit is due on `day`. Every N days is flexible: due again once N
    days have passed since it was last done (or right away when it was never done)."""
    if is_weekly(tracker):
        return True
    schedule = tracker.schedule or "daily"
    if schedule == "weekdays":
        return bool(((tracker.schedule_days or ALL_DAYS) >> day.weekday()) & 1)
    if schedule == "every_n_days":
        n = max(2, tracker.schedule_n or 2)
        return not any(_day_met(tracker, by_date.get(day - timedelta(days=k))) for k in range(1, n))
    return True


def next_due(tracker: Tracker, today: date, by_date: dict) -> date | None:
    """First day from today on which a day-period habit is due (None for week-period habits)."""
    if is_weekly(tracker):
        return None
    for k in range(0, 15):
        d = today + timedelta(days=k)
        if is_due(tracker, d, by_date):
            return d
    return None


def _first_day(tracker: Tracker, by_date: dict, today: date) -> date:
    first = min(by_date) if by_date else today
    created = tracker.created_at.date() if tracker.created_at else first
    return min(first, created)


def day_runs(tracker: Tracker, by_date: dict, today: date) -> tuple[int, int]:
    """(current, best) streak in days for a day-period habit, walking forward from its start.
    A met day adds one; a skipped or not-due day passes; a due day missed resets the run;
    today not done yet passes."""
    day = min(by_date) if by_date else today
    current = best = 0
    while day <= today:
        entry = by_date.get(day)
        if _day_met(tracker, entry):
            current += 1
            best = max(best, current)
        elif (entry is not None and entry.skipped) or day == today or not is_due(tracker, day, by_date):
            pass
        else:
            current = 0
        day += timedelta(days=1)
    return current, best


def _week_sum(entries_by_date: dict, week: date) -> float:
    return sum(e.value for d, e in entries_by_date.items() if week <= d < week + timedelta(days=7) and not e.skipped)


def _week_met(tracker: Tracker, total: float) -> bool:
    if tracker.target_value:
        return total >= tracker.target_value
    return total > 0


def week_runs(tracker: Tracker, by_date: dict, today: date) -> tuple[int, int]:
    """(current, best) streak in weeks for a week-period habit; the running week passes until met."""
    this_week = week_start_of(today)
    week = week_start_of(min(by_date)) if by_date else this_week
    current = best = 0
    while week <= this_week:
        if _week_met(tracker, _week_sum(by_date, week)):
            current += 1
            best = max(best, current)
        elif week != this_week:
            current = 0
        week += timedelta(days=7)
    return current, best


def runs(tracker: Tracker, by_date: dict, today: date) -> tuple[int, int]:
    return week_runs(tracker, by_date, today) if is_weekly(tracker) else day_runs(tracker, by_date, today)


def streak(tracker: Tracker, entries_by_date: dict, today: date) -> int:
    """Current streak: days (day-period) or weeks (week-period) met, ending today or the last period."""
    return runs(tracker, entries_by_date, today)[0]


def _cell(t: Tracker, d: date, by_date: dict, today: date) -> dict:
    e = by_date.get(d)
    return {
        "date": d.isoformat(),
        "value": e.value if e else None,
        "note": e.note if e else None,
        "status": e.status if e else None,
        "met": _day_met(t, e),
        "due": is_due(t, d, by_date),
    }


def _week_row(t: Tracker, by_date: dict, areas: dict, start: date, end: date, today: date) -> dict:
    """One tracker's row of the weekly grid: seven day cells, week total, completion and streak.
    Completion of a day-period habit is met days over the elapsed days it was due (skips left
    out); None when nothing was due yet."""
    days = [_cell(t, start + timedelta(days=i), by_date, today) for i in range(7)]
    week_total = sum((d["value"] or 0) for d in days if d["status"] != "skipped")
    if is_weekly(t):
        completion = min(1.0, week_total / t.target_value) if t.target_value else (1.0 if week_total > 0 else 0.0)
    else:
        elapsed = [d for d in days if d["date"] <= today.isoformat()]
        counted = [d for d in elapsed if d["met"] or (d["due"] and d["status"] != "skipped" and d["date"] != today.isoformat())]
        # Today counts once it is met, so a fresh morning does not read as a miss.
        completion = (sum(1 for d in counted if d["met"]) / len(counted)) if counted else None
    current, best = runs(t, by_date, today)
    area = areas.get(t.area_id)
    nd = next_due(t, today, by_date)
    return {
        **t.to_dict(),
        "area_name": area.name if area else None,
        "area_color": area.color if area else None,
        "days": days,
        "week_total": week_total,
        "week_met": _week_met(t, week_total) if is_weekly(t) else None,
        "completion": round(completion, 3) if completion is not None else None,
        "streak": current,
        "best_streak": best,
        "next_due": nd.isoformat() if nd else None,
    }


def _history_for(trackers: list[Tracker], until: date) -> dict:
    """Every entry of the given trackers up to `until`; streaks need the whole run."""
    if not trackers:
        return {}
    return entries_between([t.id for t in trackers], date(1970, 1, 1), until)


def week_row(tracker: Tracker, week_start: date | None = None) -> dict:
    """The grid row for one tracker, returned by the entry endpoints so the client can patch
    one row instead of reloading the whole week."""
    today = today_local()
    start = week_start or week_start_of(today)
    end = start + timedelta(days=6)
    by_date = _history_for([tracker], max(end, today)).get(tracker.id, {})
    areas = {a.id: a for a in db.session.scalars(select(Area)).all()}
    return _week_row(tracker, by_date, areas, start, end, today)


def week_grid(week_start: date | None = None, include_inactive: bool = False) -> dict:
    today = today_local()
    start = week_start or week_start_of(today)
    end = start + timedelta(days=6)
    trackers = list_trackers(include_inactive)
    history = _history_for(trackers, max(end, today))
    areas = {a.id: a for a in db.session.scalars(select(Area)).all()}
    rows = [_week_row(t, history.get(t.id, {}), areas, start, end, today) for t in trackers]
    return {"week_start": start.isoformat(), "week_end": end.isoformat(), "today": today.isoformat(), "trackers": rows}


def stats(tracker: Tracker) -> dict:
    """Everything the habit detail page shows: streaks, rates, a 53 week heatmap, months,
    weekdays and the notes written on check-ins."""
    today = today_local()
    by_date = _history_for([tracker], today).get(tracker.id, {})
    current, best = runs(tracker, by_date, today)
    origin = _first_day(tracker, by_date, today)
    weekly = is_weekly(tracker)

    heat_start = week_start_of(today) - timedelta(days=7 * 52)
    heatmap = []
    d = heat_start
    while d <= week_start_of(today) + timedelta(days=6):
        e = by_date.get(d)
        heatmap.append({
            "date": d.isoformat(),
            "value": e.value if e else None,
            "status": e.status if e else None,
            "met": _day_met(tracker, e),
            "due": is_due(tracker, d, by_date) if d <= today else None,
            "future": d > today,
            "before_start": d < origin,
        })
        d += timedelta(days=1)

    def day_rate(lo: date, hi: date) -> tuple[int, int]:
        """(met, counted) over [lo, hi] clipped to the habit's run, the same rule as the grid."""
        met = counted = 0
        day = max(lo, origin)
        while day <= min(hi, today):
            e = by_date.get(day)
            if _day_met(tracker, e):
                met += 1
                counted += 1
            elif day != today and is_due(tracker, day, by_date) and not (e is not None and e.skipped):
                counted += 1
            day += timedelta(days=1)
        return met, counted

    def week_rate(lo: date, hi: date) -> tuple[int, int]:
        met = counted = 0
        week = week_start_of(max(lo, origin))
        while week <= min(hi, today):
            if week >= week_start_of(lo):
                ok = _week_met(tracker, _week_sum(by_date, week))
                if ok or week != week_start_of(today):
                    counted += 1
                    met += 1 if ok else 0
            week += timedelta(days=7)
        return met, counted

    rate = week_rate if weekly else day_rate
    months = []
    first_of_month = today.replace(day=1)
    for i in range(11, -1, -1):
        y, m = first_of_month.year, first_of_month.month - i
        while m <= 0:
            y, m = y - 1, m + 12
        lo = date(y, m, 1)
        hi = (date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)) - timedelta(days=1)
        met, counted = rate(lo, hi) if hi >= origin else (0, 0)
        months.append({"month": lo.isoformat()[:7], "met": met, "counted": counted, "rate": round(met / counted, 3) if counted else None})

    weekdays = []
    if not weekly:
        for wd in range(7):
            met = counted = 0
            day = origin
            while day <= today:
                if day.weekday() == wd:
                    e = by_date.get(day)
                    if _day_met(tracker, e):
                        met, counted = met + 1, counted + 1
                    elif day != today and is_due(tracker, day, by_date) and not (e is not None and e.skipped):
                        counted += 1
                day += timedelta(days=1)
            weekdays.append({"weekday": wd, "met": met, "counted": counted, "rate": round(met / counted, 3) if counted else None})

    m30, c30 = rate(today - timedelta(days=29), today)
    mall, call = rate(origin, today)
    done_entries = [e for e in by_date.values() if not e.skipped]
    values = [e.value for e in done_entries if e.value]
    notes = [{"date": dd.isoformat(), "note": e.note, "value": e.value, "status": e.status} for dd, e in sorted(by_date.items(), reverse=True) if e.note][:50]
    nd = next_due(tracker, today, by_date)
    return {
        "tracker": tracker.to_dict(),
        "today": today.isoformat(),
        "since": origin.isoformat(),
        "unit": "week" if weekly else "day",
        "current_streak": current,
        "best_streak": best,
        "rate_30": round(m30 / c30, 3) if c30 else None,
        "rate_all": round(mall / call, 3) if call else None,
        "met_total": mall,
        "counted_total": call,
        "skipped_total": sum(1 for e in by_date.values() if e.skipped),
        "value_total": round(sum(values), 2),
        "value_avg": round(sum(values) / len(values), 2) if values else None,
        "next_due": nd.isoformat() if nd else None,
        "heatmap": heatmap,
        "months": months,
        "weekdays": weekdays,
        "notes": notes,
    }


def history(tracker: Tracker, weeks: int | None = 8) -> dict:
    """Daily points and weekly sums. weeks=None means since the tracker was created
    (or its earliest entry, whichever is older), so the chart shows the whole run."""
    today = today_local()
    if weeks is None:
        first_entry = db.session.scalar(select(func.min(TrackerEntry.date)).where(TrackerEntry.tracker_id == tracker.id))
        created = tracker.created_at.date() if tracker.created_at else today
        origin = min([d for d in (created, first_entry) if d is not None])
        weeks = max(1, (week_start_of(today) - week_start_of(origin)).days // 7 + 1)
    start = week_start_of(today) - timedelta(days=7 * (weeks - 1))
    by_date = {d: e for d, e in entries_between([tracker.id], start, today).get(tracker.id, {}).items() if not e.skipped}
    points = [{"date": d.isoformat(), "value": e.value, "note": e.note} for d, e in sorted(by_date.items())]
    weekly = []
    for i in range(weeks):
        ws = start + timedelta(days=7 * i)
        vals = [e.value for d, e in by_date.items() if ws <= d < ws + timedelta(days=7)]
        weekly.append({"week_start": ws.isoformat(), "sum": sum(vals), "avg": (sum(vals) / len(vals)) if vals else None, "count": len(vals)})
    return {"tracker": tracker.to_dict(), "from": start.isoformat(), "to": today.isoformat(), "weeks": weeks, "points": points, "weekly": weekly}


def series(weeks: int | None = 12, include_inactive: bool = False) -> dict:
    """One call for the live chart: every tracker's daily points and weekly rows over the same
    range. weeks=None spans back to the oldest tracker or entry."""
    trackers = list_trackers(include_inactive)
    today = today_local()
    if weeks is None:
        origins = [t.created_at.date() for t in trackers if t.created_at]
        first_entry = db.session.scalar(select(func.min(TrackerEntry.date)).where(TrackerEntry.tracker_id.in_([t.id for t in trackers]))) if trackers else None
        if first_entry:
            origins.append(first_entry)
        origin = min(origins) if origins else today
        weeks = max(1, (week_start_of(today) - week_start_of(origin)).days // 7 + 1)
    start = week_start_of(today) - timedelta(days=7 * (weeks - 1))
    by_tracker = entries_between([t.id for t in trackers], start, today) if trackers else {}
    # A habit counts from its creation week, or earlier when an entry was backdated. Weeks before
    # that are "not started" and stay blank on the chart; later weeks without entries plot as 0.
    first_by_tracker = dict(db.session.execute(
        select(TrackerEntry.tracker_id, func.min(TrackerEntry.date)).where(TrackerEntry.tracker_id.in_([t.id for t in trackers])).group_by(TrackerEntry.tracker_id)
    ).all()) if trackers else {}
    full = _history_for(trackers, today)
    out = []
    for t in trackers:
        every = full.get(t.id, {})
        by_date = {d: e for d, e in by_tracker.get(t.id, {}).items() if not e.skipped}
        origin = min([d for d in (t.created_at.date() if t.created_at else None, first_by_tracker.get(t.id)) if d is not None], default=start)
        first_week = week_start_of(origin)
        points = [{"date": d.isoformat(), "value": e.value} for d, e in sorted(by_date.items())]
        weekly = []
        for i in range(weeks):
            ws = start + timedelta(days=7 * i)
            days = [(d, e) for d, e in by_date.items() if ws <= d < ws + timedelta(days=7)]
            vals = [e.value for _, e in days]
            met = sum(1 for _, e in days if _met(t, e.value)) if t.type == "daily_bool" else None
            # Days the habit was due in that week, up to today (today only once done), skips
            # left out: the fair denominator for a habit that is not due every day.
            due = None
            if t.type == "daily_bool":
                due = 0
                for k in range(7):
                    d = ws + timedelta(days=k)
                    if d > today:
                        break
                    e = every.get(d)
                    if _day_met(t, e) or (d != today and is_due(t, d, every) and not (e is not None and e.skipped)):
                        due += 1
            weekly.append({"week_start": ws.isoformat(), "sum": sum(vals), "avg": (sum(vals) / len(vals)) if vals else None, "count": len(vals), "met_days": met, "due_days": due, "started": ws >= first_week})
        out.append({"tracker": t.to_dict(), "points": points, "weekly": weekly})
    return {"from": start.isoformat(), "to": today.isoformat(), "weeks": weeks, "series": out}
