"""Weekly review (plan 6.11).

`generate_review` computes the stats snapshot, asks Claude for a reflection and
next week's goal draft (kill switch `ai_enabled.weekly_review`) and falls back
to a deterministic draft. Wouter edits notes and the focus list, then
`finalize_review` creates next week's weekly_goals through A's goals service.
"""
import logging
from datetime import date, timedelta

from sqlalchemy import select

from ...extensions import db
from ...integrations import claude_client
from ...models import Area, WeeklyReview
from ...services import review_stats
from ...utils.dates import now_utc, today_local, week_start_of
from ...utils.validation import ValidationError

log = logging.getLogger(__name__)

MAX_GOALS = 5


def list_reviews(limit: int = 26) -> list[WeeklyReview]:
    return db.session.scalars(select(WeeklyReview).order_by(WeeklyReview.week_start.desc()).limit(limit)).all()


def get_review(week_start: date) -> WeeklyReview | None:
    return db.session.scalar(select(WeeklyReview).where(WeeklyReview.week_start == week_start_of(week_start)))


def deterministic_reflection(stats: dict) -> str:
    g, d, t, h = stats["goals"], stats["dos"], stats["tasks"], stats["hours"]
    lines = [f"Week of {stats['week_start']}: {g['done']} of {g['total']} weekly goals done, {t['done']} tasks completed, {h['total_hours']} hours logged."]
    if d["total"]:
        lines.append(f"Three do's: {d['done']} of {d['total']} done ({round((d['rate'] or 0) * 100)}%), {d['rolled']} rolled over.")
    slipped = [tr["name"] for tr in stats["trackers"] if tr["completion"] < 0.5]
    if slipped:
        lines.append("Habits under half: " + ", ".join(slipped) + ".")
    behind = [f"{a['area']} {a['hours']}/{a['target_hours']}h" for a in h["areas"] if a["target_hours"] and a["hours"] < a["target_hours"]]
    if behind:
        lines.append("Hours under target: " + ", ".join(behind) + ".")
    if t["overdue"]:
        lines.append(f"{t['overdue']} open task(s) are overdue.")
    return "\n\n".join(lines)


def deterministic_focus(stats: dict, max_goals: int = MAX_GOALS) -> list[dict]:
    out, seen = [], set()

    def add(title, area, reason, task_id=None, target=None):
        key = title.strip().lower()
        if key in seen or len(out) >= max_goals:
            return
        seen.add(key)
        out.append({"title": title.strip()[:200], "area": area, "target_value": target, "task_id": task_id, "reason": reason})

    for g in stats["goals"]["items"]:
        if not g["done"]:
            add(g["title"], g["area"], "Missed this week, carried over")
    for dl in stats["deadlines"]["upcoming"]:
        add(dl["title"], "Study", f"Deadline {dl['due']}", dl.get("task_id"))
    for c in stats["open_task_candidates"]:
        if c["quadrant"] == "do":
            add(c["title"], c["area"], "Urgent and important task", c["id"])
    for c in stats["open_task_candidates"]:
        if c["quadrant"] == "schedule":
            add(c["title"], c["area"], "Important task", c["id"])
    return out


def generate_review(week_start: date | None = None, force: bool = True) -> WeeklyReview:
    """Compute stats and draft reflection and focus. force=False keeps an existing draft (job idempotency)."""
    week = week_start_of(week_start or today_local())
    row = get_review(week)
    if row is not None and row.finalized:
        raise ValidationError("This review is finalized")
    if row is not None and row.generated_at is not None and not force:
        return row
    stats = review_stats.compute(week)
    answer = None
    try:
        answer = claude_client.review_week(stats, MAX_GOALS)
    except Exception:
        log.exception("review_week raised")
    if row is None:
        row = WeeklyReview(week_start=week)
        db.session.add(row)
    row.stats_json = stats
    if answer:
        row.reflection = answer["reflection"]
        row.reflection_source = "claude"
        row.next_week_focus = answer["next_week_focus"] or deterministic_focus(stats)
    else:
        row.reflection = deterministic_reflection(stats)
        row.reflection_source = "deterministic"
        row.next_week_focus = deterministic_focus(stats)
    row.generated_at = now_utc()
    db.session.commit()
    return row


def refresh_stats(row: WeeklyReview) -> WeeklyReview:
    """Recompute the numbers without touching the text (cheap, no AI)."""
    row.stats_json = review_stats.compute(row.week_start)
    db.session.commit()
    return row


def update_review(row: WeeklyReview, fields: dict) -> WeeklyReview:
    if row.finalized:
        raise ValidationError("This review is finalized")
    if "notes" in fields:
        row.notes = fields["notes"]
    if "reflection" in fields:
        row.reflection = fields["reflection"]
        row.reflection_source = "edited"
    if "next_week_focus" in fields:
        row.next_week_focus = _clean_focus(fields["next_week_focus"])
    db.session.commit()
    return row


def _clean_focus(items) -> list[dict]:
    if not isinstance(items, list):
        raise ValidationError("'next_week_focus' must be a list")
    out = []
    for item in items:
        if not isinstance(item, dict) or not str(item.get("title") or "").strip():
            raise ValidationError("Each focus item needs a 'title'")
        target = item.get("target_value")
        if target is not None:
            try:
                target = float(target)
            except (TypeError, ValueError):
                raise ValidationError("'target_value' must be a number")
        out.append(
            {
                "title": str(item["title"]).strip()[:200],
                "area": (str(item["area"]).strip() or None) if item.get("area") else None,
                "target_value": target,
                "task_id": item.get("task_id") or None,
                "reason": str(item.get("reason") or "")[:300],
            }
        )
    return out[:20]


def finalize_review(row: WeeklyReview) -> tuple[WeeklyReview, list[dict]]:
    """Create next week's weekly_goals from the focus list. Skips titles that already exist that week."""
    from ..goals import service as goals

    if row.finalized:
        raise ValidationError("This review is already finalized")
    next_week = row.week_start + timedelta(days=7)
    areas = {a.name.lower(): a.id for a in db.session.scalars(select(Area)).all()}
    existing = {g.title.strip().lower() for g in goals.list_goals(next_week)}
    created = []
    for item in row.next_week_focus or []:
        title = str(item.get("title") or "").strip()
        if not title or title.lower() in existing:
            continue
        goal = goals.create_goal(
            {
                "title": title,
                "area_id": areas.get((item.get("area") or "").lower()),
                "target_value": item.get("target_value"),
                "week_start": next_week,
                "notes": item.get("reason") or None,
            }
        )
        existing.add(title.lower())
        created.append(goal.to_dict())
    row.finalized = True
    row.finalized_at = now_utc()
    db.session.commit()
    return row, created
