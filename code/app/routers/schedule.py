# code/app/routers/schedule.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import db_models, models, schemas, weeks
from app.database import get_db
from app.placement import readable_messages, replace_blocks, to_solver_input
from app.solver import place_flexible_tasks, solve_week

router = APIRouter(prefix="/schedule", tags=["schedule"])

DAYS = [d.value for d in db_models.DayOfWeek]
SLOTS_PER_DAY = 12


def _grid_response(db: Session, warnings: list[str] | None = None) -> schemas.ScheduleSolveResult:
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
                    status=weeks.current_status(block),
                )
            )
    return schemas.ScheduleSolveResult(slots=slots, warnings=warnings or [])


@router.get("", response_model=schemas.ScheduleSolveResult)
def get_schedule(db: Session = Depends(get_db)):
    """Returns the current schedule grid without re-solving."""
    return _grid_response(db)


@router.post("/solve", response_model=schemas.ScheduleSolveResult)
def solve_schedule(db: Session = Depends(get_db)):
    """Runs the full 4-pass constraint solver against all active commitments
    and persists the result, replacing any previously auto-planned blocks.
    Logged blocks stay put and count towards their commitments."""
    commitments = db.query(db_models.Commitment).all()
    if not commitments:
        raise HTTPException(status_code=422, detail="No commitments to schedule")

    solver_input = [to_solver_input(c) for c in commitments]
    try:
        warnings = replace_blocks(db, commitments, lambda grid: solve_week(solver_input, grid))
    except ValueError as exc:
        detail = readable_messages(db, [str(exc)])[0]
        db.rollback()
        raise HTTPException(status_code=422, detail=detail) from exc

    db.commit()
    return _grid_response(db, warnings)


@router.post("/reslot-flexible", response_model=schemas.ScheduleSolveResult)
def reslot_flexible_tasks(db: Session = Depends(get_db)):
    """Manual-override support: keeps every existing block in place (fixed
    events, recurring quotas, deadlines, and any manually dragged block) and
    only recomputes placement for FLEXIBLE_TASK commitments into the slots
    that remain open."""
    commitments = db.query(db_models.Commitment).all()
    flexible = [c for c in commitments if c.type == models.CommitmentType.FLEXIBLE_TASK]
    solver_tasks = [to_solver_input(c) for c in flexible]
    warnings = replace_blocks(db, flexible, lambda grid: place_flexible_tasks(grid, solver_tasks))
    db.commit()
    return _grid_response(db, warnings)
