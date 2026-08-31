# code/app/solver.py
from typing import List
from app.models import Commitment, CommitmentType, ScheduleGrid

def place_fixed_events(grid: ScheduleGrid, events: List[Commitment]) -> ScheduleGrid:
    """Places fixed commitments into the weekly schedule grid."""
    for event in events:
        if event.commitment_type == CommitmentType.FIXED_EVENT:
            if event.day is not None and event.slot_index is not None:
                for slot in grid.slots:
                    if slot.day == event.day and slot.slot_index == event.slot_index:
                        slot.occupied_by = event.title
                        break
    return grid
