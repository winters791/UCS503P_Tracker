# code/app/placement.py
"""Auto-placement of a single commitment onto the persisted grid.

Reuses the solver passes so the placement rules live in one place: a
FIXED_EVENT lands on its day/slot, a RECURRING_QUOTA spreads across the
week at its preferred slot, a HARD_DEADLINE is backward-scheduled from
its cutoff. FLEXIBLE_TASK is deliberately left alone - those are owned by
the re-slot action, which packs all of them into whatever gaps remain.
"""
from sqlalchemy.orm import Session

from app import db_models, models
from app.solver import place_fixed_events, place_hard_deadlines, place_recurring_quotas

OCCUPIED = "__occupied__"
PLACEMENT_FIELDS = {
    "type",
    "day",
    "slot_index",
    "deadline_day",
    "deadline_slot",
    "target_per_week",
    "duration_blocks",
}


def _has_placement_info(c: db_models.Commitment) -> bool:
    if c.type == models.CommitmentType.FIXED_EVENT:
        return c.day is not None and c.slot_index is not None
    if c.type == models.CommitmentType.RECURRING_QUOTA:
        return c.target_per_week is not None
    if c.type == models.CommitmentType.HARD_DEADLINE:
        return c.deadline_day is not None and c.deadline_slot is not None
    return False


def clear_planned_blocks(db: Session, commitment: db_models.Commitment) -> None:
    """Drops this commitment's PLANNED blocks so it can be re-placed.
    Completed/missed blocks are history and are never touched."""
    db.query(db_models.ScheduledBlock).filter(
        db_models.ScheduledBlock.commitment_id == commitment.id,
        db_models.ScheduledBlock.status == db_models.BlockStatus.PLANNED,
    ).delete(synchronize_session=False)
    db.flush()


def auto_place(db: Session, commitment: db_models.Commitment) -> int:
    """Creates PLANNED blocks for the commitment around everything already on
    the grid. Returns the number of blocks placed (0 when the commitment has
    no placement info yet, e.g. a fixed event without a day - the user can
    still drag it on manually). Raises ValueError on a slot conflict or
    insufficient capacity, mirroring the solver."""
    if not _has_placement_info(commitment):
        return 0

    occupied = {
        (b.day_of_week.value, b.slot_index)
        for b in db.query(db_models.ScheduledBlock).all()
    }
    grid = models.ScheduleGrid.create_empty_week()
    for slot in grid.slots:
        if (slot.day, slot.slot_index) in occupied:
            slot.occupied_by = OCCUPIED

    solver_input = models.Commitment(
        id=commitment.id,
        title=commitment.id,  # solver writes title into occupied_by; keep it mappable
        commitment_type=commitment.type,
        day=commitment.day.value if commitment.day else None,
        slot_index=commitment.slot_index,
        target_frequency=commitment.target_per_week,
        deadline_day=commitment.deadline_day.value if commitment.deadline_day else None,
        deadline_slot=commitment.deadline_slot,
        required_blocks=commitment.duration_blocks,
        priority=commitment.priority,
    )

    if commitment.type == models.CommitmentType.FIXED_EVENT:
        grid = place_fixed_events(grid, [solver_input])
    elif commitment.type == models.CommitmentType.RECURRING_QUOTA:
        grid = place_recurring_quotas(grid, [solver_input])
    elif commitment.type == models.CommitmentType.HARD_DEADLINE:
        grid = place_hard_deadlines(grid, [solver_input])

    placed = 0
    for slot in grid.slots:
        if slot.occupied_by != commitment.id:
            continue
        db.add(
            db_models.ScheduledBlock(
                commitment_id=commitment.id,
                slot_index=slot.slot_index,
                day_of_week=db_models.DayOfWeek(slot.day),
                status=db_models.BlockStatus.PLANNED,
            )
        )
        placed += 1
    db.flush()
    return placed
