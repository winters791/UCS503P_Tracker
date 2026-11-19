# code/app/placement.py
"""Placing commitments onto the persisted grid.

Reuses the solver passes so the placement rules live in one place: a
FIXED_EVENT lands on its day/slot, a RECURRING_QUOTA spreads across the
week at its preferred slot, a HARD_DEADLINE is backward-scheduled from
its cutoff - each within its constraint rules. FLEXIBLE_TASK is left to
the re-slot action, which packs all of them into whatever gaps remain.

Every re-placement goes through replace_blocks, which keeps this week's
logged blocks where they are and moves the commitment's other block rows
rather than deleting them, so execution-log history stays attached.
"""
from typing import Callable

from sqlalchemy.orm import Session

from app import db_models, models, weeks
from app.solver import place_fixed_events, place_hard_deadlines, place_recurring_quotas

PLACEMENT_FIELDS = {
    "type",
    "day",
    "slot_index",
    "deadline_day",
    "deadline_slot",
    "target_per_week",
    "duration_blocks",
}


def to_solver_input(c: db_models.Commitment) -> models.Commitment:
    """Converts a stored commitment (and its constraint rules) for the solver.
    The solver writes `title` into occupied_by, so the id goes there to keep
    every placed cell mappable back to its commitment."""
    return models.Commitment(
        id=c.id,
        title=c.id,
        commitment_type=c.type,
        day=c.day.value if c.day else None,
        slot_index=c.slot_index,
        target_frequency=c.target_per_week,
        deadline_day=c.deadline_day.value if c.deadline_day else None,
        deadline_slot=c.deadline_slot,
        required_blocks=c.duration_blocks,
        priority=c.priority,
        rules=[
            models.SchedulingRule(
                rule_type=r.rule_type,
                target_slot=r.target_slot,
                hard=r.strictness == db_models.Strictness.HARD,
            )
            for r in c.constraint_rules
        ],
    )


def readable_messages(db: Session, messages: list[str]) -> list[str]:
    """Solver warnings and errors quote the occupied_by value, which is a
    commitment id - swap ids back to titles before showing them to anyone.
    Call before any rollback, while a just-added commitment is still visible."""
    titles = {c.id: c.title for c in db.query(db_models.Commitment).all()}
    out = []
    for message in messages:
        for cid, title in titles.items():
            message = message.replace(f"'{cid}'", f"'{title}'")
        out.append(message)
    return out


def has_placement_info(c: db_models.Commitment) -> bool:
    if c.type == models.CommitmentType.FIXED_EVENT:
        return c.day is not None and c.slot_index is not None
    if c.type == models.CommitmentType.RECURRING_QUOTA:
        return c.target_per_week is not None
    if c.type == models.CommitmentType.HARD_DEADLINE:
        return c.deadline_day is not None and c.deadline_slot is not None
    return False


def replace_blocks(
    db: Session,
    targets: list[db_models.Commitment],
    place: Callable[[models.ScheduleGrid], models.ScheduleGrid],
) -> list[str]:
    """Re-places the target commitments' blocks with `place`.

    Blocks marked done/missed/skipped this week stay put and count towards
    their commitment (the solver sees their cells as already owned). Every
    other block of a target is free to move. Freed rows are reused for the
    new cells - ones with execution logs first - and only surplus rows are
    deleted, so history survives re-placement. Returns readable solver
    warnings; raises ValueError like the solver does."""
    target_ids = {c.id for c in targets}
    movable: dict[str, list[db_models.ScheduledBlock]] = {cid: [] for cid in target_ids}
    owners: dict[tuple[str, int], str] = {}
    for block in db.query(db_models.ScheduledBlock).all():
        if block.commitment_id in target_ids and weeks.current_status(block) == db_models.BlockStatus.PLANNED:
            movable[block.commitment_id].append(block)
        else:
            owners[(block.day_of_week.value, block.slot_index)] = block.commitment_id

    grid = models.ScheduleGrid.create_empty_week()
    for slot in grid.slots:
        slot.occupied_by = owners.get((slot.day, slot.slot_index))
    result = place(grid.model_copy(deep=True))

    new_cells: dict[str, list[tuple[str, int]]] = {cid: [] for cid in target_ids}
    for slot in result.slots:
        if slot.occupied_by in target_ids and (slot.day, slot.slot_index) not in owners:
            new_cells[slot.occupied_by].append((slot.day, slot.slot_index))

    for cid in target_ids:
        rows = sorted(movable[cid], key=lambda b: not b.execution_logs)
        cells = new_cells[cid]
        for row, (day, slot_index) in zip(rows, cells):
            row.day_of_week = db_models.DayOfWeek(day)
            row.slot_index = slot_index
            row.status = db_models.BlockStatus.PLANNED
            row.status_updated_at = None
        for day, slot_index in cells[len(rows):]:
            db.add(
                db_models.ScheduledBlock(
                    commitment_id=cid,
                    slot_index=slot_index,
                    day_of_week=db_models.DayOfWeek(day),
                    status=db_models.BlockStatus.PLANNED,
                )
            )
        for row in rows[len(cells):]:
            db.delete(row)
    db.flush()
    return readable_messages(db, result.warnings)


def auto_place(db: Session, commitment: db_models.Commitment) -> list[str]:
    """(Re-)places one commitment around everything else on the grid,
    honouring its constraint rules. With no placement info yet (e.g. a fixed
    event without a day, or any flexible task) its movable blocks are simply
    cleared - the user can still drag it on manually. Returns solver
    warnings, such as a soft rule that had to be relaxed. Raises ValueError
    on a slot conflict, insufficient capacity, or an unsatisfiable hard rule."""
    solver_input = to_solver_input(commitment)

    def place(grid: models.ScheduleGrid) -> models.ScheduleGrid:
        if not has_placement_info(commitment):
            return grid
        if commitment.type == models.CommitmentType.FIXED_EVENT:
            return place_fixed_events(grid, [solver_input])
        if commitment.type == models.CommitmentType.RECURRING_QUOTA:
            return place_recurring_quotas(grid, [solver_input])
        return place_hard_deadlines(grid, [solver_input])

    return replace_blocks(db, [commitment], place)
