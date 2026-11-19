# code/app/insights.py
"""Weekly consistency, streaks and the end-of-week retrospective.

The grid is a single weekly template, so history comes from execution logs:
each log is dated, and its local calendar week (Monday start) decides which
week it counts towards. When a block is logged more than once in a week, the
latest log wins - re-marking a "missed" block as done fixes the record rather
than double counting.

Everything here works on plain dataclasses so it can be tested without a
database; routers/insights.py does the loading.
"""
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Optional

from app.models import CommitmentType
from app.solver import BAND_NAMES, DAYS, TIME_BANDS
from app.weeks import week_start

DAY_START_HOUR = 8  # slot 0 starts at 08:00, one slot per hour
STREAK_LOOKBACK_WEEKS = 104


@dataclass
class Item:
    id: str
    title: str
    type: CommitmentType
    target_per_week: Optional[int] = None


@dataclass
class Block:
    id: str
    commitment_id: str
    day_index: int  # 0 = Monday
    slot_index: int


@dataclass
class Log:
    block_id: str
    completed: bool
    logged_at: datetime  # local time


def _outcomes(logs: list[Log]) -> dict[tuple[date, str], bool]:
    """(week_start, block_id) -> completed, using the latest log in that week."""
    latest: dict[tuple[date, str], Log] = {}
    for log in logs:
        key = (week_start(log.logged_at.date()), log.block_id)
        if key not in latest or log.logged_at >= latest[key].logged_at:
            latest[key] = log
    return {key: log.completed for key, log in latest.items()}


def _completed_per_week(outcomes, block_ids: set[str]) -> dict[date, int]:
    counts: dict[date, int] = {}
    for (week, block_id), completed in outcomes.items():
        if completed and block_id in block_ids:
            counts[week] = counts.get(week, 0) + 1
    return counts


# ---- consistency -------------------------------------------------------------

@dataclass
class WeekResult:
    week_start: date
    completed: int
    met: bool


@dataclass
class QuotaConsistency:
    commitment_id: str
    title: str
    target: int
    completed_this_week: int
    streak: int
    history: list[WeekResult] = field(default_factory=list)


def consistency(
    items: list[Item], blocks: list[Block], logs: list[Log], today: date, weeks: int = 8
) -> list[QuotaConsistency]:
    """Weekly volume for every recurring quota, plus a forgiving streak.

    The streak counts consecutive weeks that met the target. Only a closed
    week can break it: the current week adds one as soon as the target is
    hit, but falling short mid-week costs nothing - there is still time."""
    outcomes = _outcomes(logs)
    this_week = week_start(today)
    results = []
    for item in items:
        if item.type != CommitmentType.RECURRING_QUOTA or not item.target_per_week:
            continue
        target = item.target_per_week
        block_ids = {b.id for b in blocks if b.commitment_id == item.id}
        per_week = _completed_per_week(outcomes, block_ids)

        streak = 1 if per_week.get(this_week, 0) >= target else 0
        week = this_week - timedelta(weeks=1)
        for _ in range(STREAK_LOOKBACK_WEEKS):
            if per_week.get(week, 0) < target:
                break
            streak += 1
            week -= timedelta(weeks=1)

        history = []
        for back in range(weeks - 1, -1, -1):
            w = this_week - timedelta(weeks=back)
            done = per_week.get(w, 0)
            history.append(WeekResult(week_start=w, completed=done, met=done >= target))

        results.append(
            QuotaConsistency(
                commitment_id=item.id,
                title=item.title,
                target=target,
                completed_this_week=per_week.get(this_week, 0),
                streak=streak,
                history=history,
            )
        )
    return results


# ---- retrospective -----------------------------------------------------------

@dataclass
class Tally:
    planned: int = 0
    completed: int = 0
    missed: int = 0
    not_logged: int = 0
    upcoming: int = 0

    @property
    def due(self) -> int:
        """Blocks whose time has come - the ones that count towards the rate."""
        return self.completed + self.missed + self.not_logged

    def add(self, outcome: str) -> None:
        self.planned += 1
        setattr(self, outcome, getattr(self, outcome) + 1)


@dataclass
class CommitmentTally:
    commitment_id: str
    title: str
    type: CommitmentType
    tally: Tally


@dataclass
class QuotaResult:
    title: str
    completed: int
    target: int
    met: bool


@dataclass
class Retrospective:
    week_start: date
    week_end: date
    totals: Tally
    by_commitment: list[CommitmentTally]
    by_day: list[Tally]
    quota_results: list[QuotaResult]
    highlights: list[str]


def _block_start(week: date, block: Block, tz) -> datetime:
    day = week + timedelta(days=block.day_index)
    return datetime.combine(day, time(DAY_START_HOUR + block.slot_index), tzinfo=tz)


def retrospective(
    items: list[Item], blocks: list[Block], logs: list[Log], week: date, now: datetime
) -> Retrospective:
    """Planned vs done for one week. A block nobody logged counts as
    "not logged" once its start time has passed and "upcoming" before that,
    so a review in the middle of the week is not full of false misses."""
    week = week_start(week)
    outcomes = _outcomes(logs)
    items_by_id = {i.id: i for i in items}

    totals = Tally()
    by_day = [Tally() for _ in DAYS]
    # Timetables often store each lecture as its own commitment with a shared
    # title; review them as one row.
    by_item: dict[tuple[str, CommitmentType], Tally] = {}
    first_id: dict[tuple[str, CommitmentType], str] = {}
    not_done_by_band = {band: 0 for band in TIME_BANDS}

    for block in blocks:
        if block.commitment_id not in items_by_id:
            continue
        logged = outcomes.get((week, block.id))
        if logged is True:
            outcome = "completed"
        elif logged is False:
            outcome = "missed"
        elif _block_start(week, block, now.tzinfo) <= now:
            outcome = "not_logged"
        else:
            outcome = "upcoming"
        totals.add(outcome)
        by_day[block.day_index].add(outcome)
        item = items_by_id[block.commitment_id]
        key = (item.title, item.type)
        first_id.setdefault(key, item.id)
        by_item.setdefault(key, Tally()).add(outcome)
        if outcome in ("missed", "not_logged"):
            band = next(b for b, slots in TIME_BANDS.items() if block.slot_index in slots)
            not_done_by_band[band] += 1

    type_order = list(CommitmentType)
    by_commitment = sorted(
        (CommitmentTally(first_id[key], key[0], key[1], tally) for key, tally in by_item.items()),
        key=lambda c: (type_order.index(c.type), c.title.lower()),
    )

    quota_results = []
    for c in by_commitment:
        target = items_by_id[c.commitment_id].target_per_week
        if c.type == CommitmentType.RECURRING_QUOTA and target:
            quota_results.append(QuotaResult(c.title, c.tally.completed, target, c.tally.completed >= target))

    return Retrospective(
        week_start=week,
        week_end=week + timedelta(days=6),
        totals=totals,
        by_commitment=by_commitment,
        by_day=by_day,
        quota_results=quota_results,
        highlights=_highlights(totals, by_commitment, by_day, quota_results, not_done_by_band),
    )


def _highlights(totals, by_commitment, by_day, quota_results, not_done_by_band) -> list[str]:
    if totals.due == 0:
        return ["Nothing to review yet - no blocks have come due this week."]

    lines = [
        f"Completed {totals.completed} of {totals.due} blocks that were due "
        f"({round(100 * totals.completed / totals.due)}%)."
    ]

    worst = max(by_commitment, key=lambda c: c.tally.missed + c.tally.not_logged)
    not_done = worst.tally.missed + worst.tally.not_logged
    if not_done:
        lines.append(f"{worst.title} slipped the most: {not_done} of {worst.tally.due} not done.")

    days_due = [(DAYS[i], t) for i, t in enumerate(by_day) if t.due]
    if len(days_due) >= 2:
        day, t = min(days_due, key=lambda d: d[1].completed / d[1].due)
        if t.completed < t.due:
            lines.append(f"{day} was the weakest day ({t.completed}/{t.due} done).")

    band, misses = max(not_done_by_band.items(), key=lambda kv: kv[1])
    if misses >= 2:
        lines.append(f"Most misses happened in the {BAND_NAMES[band]} ({misses}).")

    if quota_results:
        met = sum(q.met for q in quota_results)
        short = ", ".join(f"{q.title} {q.completed}/{q.target}" for q in quota_results if not q.met)
        lines.append(
            f"Hit {met} of {len(quota_results)} weekly targets" + (f" - short on {short}." if short else ".")
        )

    if totals.not_logged:
        lines.append(f"{totals.not_logged} past block(s) were never logged.")
    return lines
