"""AI spend from `ai_calls` (plan 4.3: spending visible on the homepage).

Live numbers come straight from the table; the nightly `ai_cost_rollup` job
stores one compact entry per day in Settings `ai_spend_daily` so history stays
available if ai_calls is ever pruned.
"""
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select

from ...extensions import db
from ...models import AiCall, Setting
from ...settings_defaults import get_setting
from ...utils.dates import app_tz, iso, today_local

ROLLUP_KEY = "ai_spend_daily"
ROLLUP_KEEP_DAYS = 90


def _bounds(start_day: date, end_day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(start_day, time.min, tzinfo=app_tz()).astimezone(timezone.utc)
    end = datetime.combine(end_day + timedelta(days=1), time.min, tzinfo=app_tz()).astimezone(timezone.utc)
    return start, end


def _money(value) -> float:
    return float(Decimal(value or 0).quantize(Decimal("0.000001")))


def totals_between(start_day: date, end_day: date) -> dict:
    start, end = _bounds(start_day, end_day)
    rows = db.session.execute(
        select(AiCall.feature, AiCall.model, AiCall.ok, func.count(), func.sum(AiCall.cost_estimate), func.sum(AiCall.input_tokens), func.sum(AiCall.output_tokens))
        .where(AiCall.created_at >= start, AiCall.created_at < end)
        .group_by(AiCall.feature, AiCall.model, AiCall.ok)
    ).all()
    by_feature: dict = {}
    by_model: dict = {}
    total = Decimal(0)
    calls = failed = 0
    for feature, model, ok, n, cost, tin, tout in rows:
        cost = Decimal(cost or 0)
        total += cost
        calls += n
        if not ok:
            failed += n
        f = by_feature.setdefault(feature, {"feature": feature, "calls": 0, "failed": 0, "cost": Decimal(0), "input_tokens": 0, "output_tokens": 0})
        f["calls"] += n
        f["failed"] += 0 if ok else n
        f["cost"] += cost
        f["input_tokens"] += int(tin or 0)
        f["output_tokens"] += int(tout or 0)
        m = by_model.setdefault(model, {"model": model, "calls": 0, "cost": Decimal(0)})
        m["calls"] += n
        m["cost"] += cost
    return {
        "from": start_day.isoformat(),
        "to": end_day.isoformat(),
        "cost": _money(total),
        "calls": calls,
        "failed": failed,
        "by_feature": sorted(({**f, "cost": _money(f["cost"])} for f in by_feature.values()), key=lambda f: -f["cost"]),
        "by_model": sorted(({**m, "cost": _money(m["cost"])} for m in by_model.values()), key=lambda m: -m["cost"]),
    }


def per_day(start_day: date, end_day: date) -> list[dict]:
    start, end = _bounds(start_day, end_day)
    rows = db.session.scalars(select(AiCall).where(AiCall.created_at >= start, AiCall.created_at < end)).all()
    buckets: dict = {}
    for r in rows:
        day = r.created_at.replace(tzinfo=timezone.utc).astimezone(app_tz()).date().isoformat() if r.created_at.tzinfo is None else r.created_at.astimezone(app_tz()).date().isoformat()
        b = buckets.setdefault(day, {"date": day, "cost": Decimal(0), "calls": 0})
        b["cost"] += Decimal(r.cost_estimate or 0)
        b["calls"] += 1
    out = []
    d = start_day
    while d <= end_day:
        b = buckets.get(d.isoformat(), {"date": d.isoformat(), "cost": Decimal(0), "calls": 0})
        out.append({**b, "cost": _money(b["cost"])})
        d += timedelta(days=1)
    return out


def summary() -> dict:
    today = today_local()
    month_start = today.replace(day=1)
    month = totals_between(month_start, today)
    recent = db.session.scalars(select(AiCall).order_by(AiCall.created_at.desc()).limit(10)).all()
    return {
        "today": today.isoformat(),
        "month": month,
        "today_cost": totals_between(today, today)["cost"],
        "last_7_days": per_day(today - timedelta(days=6), today),
        "budget_usd": get_setting("ai_monthly_budget_usd"),
        "recent": [
            {"id": str(r.id), "feature": r.feature, "model": r.model, "ok": r.ok, "cost": _money(r.cost_estimate), "input_tokens": r.input_tokens, "output_tokens": r.output_tokens, "error": (r.error or "")[:200] or None, "created_at": iso(r.created_at)}
            for r in recent
        ],
    }


def rollup_day(day: date) -> dict:
    """Store the day's totals under Settings ai_spend_daily[day]. Overwrites, so re-running is safe."""
    t = totals_between(day, day)
    entry = {"cost": t["cost"], "calls": t["calls"], "failed": t["failed"], "by_feature": {f["feature"]: f["cost"] for f in t["by_feature"]}}
    row = db.session.scalar(select(Setting).where(Setting.key == ROLLUP_KEY))
    data = dict(row.value) if row is not None and isinstance(row.value, dict) else {}
    data[day.isoformat()] = entry
    cutoff = (day - timedelta(days=ROLLUP_KEEP_DAYS)).isoformat()
    data = {k: v for k, v in data.items() if k >= cutoff}
    if row is None:
        db.session.add(Setting(key=ROLLUP_KEY, value=data))
    else:
        row.value = data
    db.session.commit()
    return entry
