# code/app/routers/insights.py
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import db_models, insights, schemas
from app import weeks as clock
from app.database import get_db

router = APIRouter(prefix="/insights", tags=["insights"])

DAY_INDEX = {d: i for i, d in enumerate(db_models.DayOfWeek)}


def _load(db: Session):
    items = [
        insights.Item(c.id, c.title, c.type, c.target_per_week)
        for c in db.query(db_models.Commitment).all()
    ]
    blocks = [
        insights.Block(b.id, b.commitment_id, DAY_INDEX[b.day_of_week], b.slot_index)
        for b in db.query(db_models.ScheduledBlock).all()
    ]
    logs = [
        insights.Log(log.block_id, log.completed, clock.to_local(log.logged_at))
        for log in db.query(db_models.ExecutionLog).all()
    ]
    return items, blocks, logs


@router.get("/consistency", response_model=schemas.ConsistencyReport)
def get_consistency(weeks: int = Query(8, ge=1, le=52), db: Session = Depends(get_db)):
    """Completed vs target per recurring quota for the current week, the last
    `weeks` weeks of history, and the rolling streak."""
    today = clock.now().date()
    items, blocks, logs = _load(db)
    return schemas.ConsistencyReport(
        week_start=clock.week_start(today),
        quotas=insights.consistency(items, blocks, logs, today, weeks),
    )


@router.get("/retrospective", response_model=schemas.RetrospectiveReport)
def get_retrospective(week_start: Optional[date] = None, db: Session = Depends(get_db)):
    """Planned vs done for the week containing `week_start` (default: this week)."""
    current = clock.now()
    items, blocks, logs = _load(db)
    return insights.retrospective(items, blocks, logs, week_start or current.date(), current)
