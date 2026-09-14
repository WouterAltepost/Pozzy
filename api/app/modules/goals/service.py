"""Weekly goals."""
from datetime import date

from sqlalchemy import select

from ...extensions import db
from ...models import Area, WeeklyGoal
from ...utils.dates import today_local, week_start_of
from ...utils.validation import ValidationError, to_uuid


def _check_area(area_id):
    if area_id is not None and db.session.get(Area, area_id) is None:
        raise ValidationError("'area_id' does not match an area")


def list_goals(week_start: date | None = None) -> list[WeeklyGoal]:
    start = week_start or week_start_of(today_local())
    stmt = select(WeeklyGoal).where(WeeklyGoal.week_start == start).order_by(WeeklyGoal.done, WeeklyGoal.created_at)
    return db.session.scalars(stmt).all()


def create_goal(fields: dict) -> WeeklyGoal:
    _check_area(fields.get("area_id"))
    fields["week_start"] = week_start_of(fields.get("week_start") or today_local())
    goal = WeeklyGoal(**fields)
    _auto_done(goal)
    db.session.add(goal)
    db.session.commit()
    return goal


def update_goal(goal: WeeklyGoal, fields: dict) -> WeeklyGoal:
    if "area_id" in fields:
        _check_area(fields["area_id"])
    if "week_start" in fields and fields["week_start"]:
        fields["week_start"] = week_start_of(fields["week_start"])
    explicit_done = "done" in fields
    for key, value in fields.items():
        setattr(goal, key, value)
    if not explicit_done:
        _auto_done(goal)
    db.session.commit()
    return goal


def _auto_done(goal: WeeklyGoal) -> None:
    """A goal with a target flips to done when the target is reached."""
    if goal.target_value and (goal.current_value or 0) >= goal.target_value:
        goal.done = True


def add_progress(goal: WeeklyGoal, delta: float) -> WeeklyGoal:
    goal.current_value = max(0.0, (goal.current_value or 0) + delta)
    _auto_done(goal)
    db.session.commit()
    return goal


def delete_goal(goal: WeeklyGoal) -> None:
    db.session.delete(goal)
    db.session.commit()


def get_goal(goal_id) -> WeeklyGoal | None:
    key = to_uuid(goal_id)
    return db.session.get(WeeklyGoal, key) if key else None


def week_summary(week_start: date | None = None) -> dict:
    goals = list_goals(week_start)
    return {"total": len(goals), "done": sum(1 for g in goals if g.done)}
