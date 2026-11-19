# code/app/weeks.py
"""What "this week" means. The grid is one weekly template; a block's status
(completed, missed, skipped) belongs to the week it was set in, and the block
reads as PLANNED again from the next Monday. Weeks follow the user's local
clock, Monday first. Timestamps are stored as naive UTC, like logged_at."""
from datetime import UTC, date, datetime, timedelta

from app import db_models


def now() -> datetime:
    """Local, timezone-aware. Tests monkeypatch this to travel in time."""
    return datetime.now().astimezone()


def utc_stamp() -> datetime:
    """A timestamp in the stored form: naive UTC."""
    return now().astimezone(UTC).replace(tzinfo=None)


def to_local(stored: datetime) -> datetime:
    if stored.tzinfo is None:
        stored = stored.replace(tzinfo=UTC)
    return stored.astimezone(now().tzinfo)


def week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def this_week() -> date:
    return week_start(now().date())


def current_status(block: db_models.ScheduledBlock) -> db_models.BlockStatus:
    """The block's status for the current week - PLANNED once the week it was
    marked in is over."""
    if block.status == db_models.BlockStatus.PLANNED or block.status_updated_at is None:
        return db_models.BlockStatus.PLANNED
    if week_start(to_local(block.status_updated_at).date()) != this_week():
        return db_models.BlockStatus.PLANNED
    return block.status
