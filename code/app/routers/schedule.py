# code/app/routers/schedule.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import db_models, models, schemas
from app.database import get_db
from app.solver import place_flexible_tasks, solve_week

router = APIRouter(prefix="/schedule", tags=["schedule"])

DAYS = [d.value for d in db_models.DayOfWeek]
SLOTS_PER_DAY = 12
REGENERABLE_STATUSES = {db_models.BlockStatus.PLANNED}


def _grid_response(db: Session) -> schemas.ScheduleSolveResult:
    commitments_by_id = {c.id: c for c in db.query(db_models.Commitment).all()}
    blocks = db.query(db_models.ScheduledBlock).all()
    blocks_by_key = {(b.day_of_week.value, b.slot_index): b for b in blocks}

    slots: list[schemas.ScheduleSlotOut] = []
    for day in DAYS:
        for slot_index in range(SLOTS_PER_DAY):
            block = blocks_by_key.get((day, slot_index))
            if block is None:
                slots.append(
                    schemas.ScheduleSlotOut(day_of_week=day, slot_index=slot_index)
                )
                continue
            commitment = commitments_by_id.get(block.commitment_id)
            slots.append(
                schemas.ScheduleSlotOut(
                    day_of_week=day,
                    slot_index=slot_index,
                    block_id=block.id,
                    commitment_id=block.commitment_id,
                    commitment_title=commitment.title if commitment else None,
                    commitment_type=commitment.type if commitment else None,
                    status=block.status,
                )
            )
    return schemas.ScheduleSolveResult(slots=slots, warnings=[])


@router.get("", response_model=schemas.ScheduleSolveResult)
def get_schedule(db: Session = Depends(get_db)):
    """Returns the current schedule grid without re-solving."""
    return _grid_response(db)


@router.post("/solve", response_model=schemas.ScheduleSolveResult)
def solve_schedule(db: Session = Depends(get_db)):
    """Runs the full 4-pass constraint solver against all active commitments
    and persists the result, replacing any previously auto-planned blocks."""
    commitments = db.query(db_models.Commitment).all()
    if not commitments:
        raise HTTPException(status_code=422, detail="No commitments to schedule")

    solver_input = [
        models.Commitment(
            id=c.id,
            title=c.id,  # keep the commitment id in occupied_by so we can map it back
            commitment_type=c.type,
            day=c.day.value if c.day else None,
            slot_index=c.slot_index,
            target_frequency=c.target_per_week,
            deadline_day=c.deadline_day.value if c.deadline_day else None,
            deadline_slot=c.deadline_slot,
            required_blocks=c.duration_blocks,
            priority=c.priority,
        )
        for c in commitments
    ]

    try:
        grid = solve_week(solver_input)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    db.query(db_models.ScheduledBlock).filter(
        db_models.ScheduledBlock.status.in_(REGENERABLE_STATUSES)
    ).delete(synchronize_session=False)
    db.flush()

    for slot in grid.slots:
        if slot.occupied_by is None:
            continue
        db.add(
            db_models.ScheduledBlock(
                commitment_id=slot.occupied_by,
                slot_index=slot.slot_index,
                day_of_week=db_models.DayOfWeek(slot.day),
                status=db_models.BlockStatus.PLANNED,
            )
        )

    db.commit()
    return _grid_response(db)


@router.post("/reslot-flexible", response_model=schemas.ScheduleSolveResult)
def reslot_flexible_tasks(db: Session = Depends(get_db)):
    """Manual-override support: keeps every existing block in place (fixed
    events, recurring quotas, deadlines, and any manually dragged block) and
    only recomputes placement for FLEXIBLE_TASK commitments into the slots
    that remain open."""
    commitments = db.query(db_models.Commitment).all()
    flexible = [c for c in commitments if c.type == models.CommitmentType.FLEXIBLE_TASK]
    flexible_ids = {c.id for c in flexible}

    db.query(db_models.ScheduledBlock).filter(
        db_models.ScheduledBlock.commitment_id.in_(flexible_ids),
        db_models.ScheduledBlock.status.in_(REGENERABLE_STATUSES),
    ).delete(synchronize_session=False)
    db.flush()

    occupied_keys = {
        (b.day_of_week.value, b.slot_index) for b in db.query(db_models.ScheduledBlock).all()
    }

    grid = models.ScheduleGrid.create_empty_week()
    for slot in grid.slots:
        if (slot.day, slot.slot_index) in occupied_keys:
            slot.occupied_by = "__occupied__"

    solver_tasks = [
        models.Commitment(
            id=c.id,
            title=c.id,
            commitment_type=c.type,
            required_blocks=c.duration_blocks,
            priority=c.priority,
        )
        for c in flexible
    ]
    grid = place_flexible_tasks(grid, solver_tasks)

    for slot in grid.slots:
        if slot.occupied_by is None or slot.occupied_by == "__occupied__":
            continue
        db.add(
            db_models.ScheduledBlock(
                commitment_id=slot.occupied_by,
                slot_index=slot.slot_index,
                day_of_week=db_models.DayOfWeek(slot.day),
                status=db_models.BlockStatus.PLANNED,
            )
        )

    db.commit()
    return _grid_response(db)
