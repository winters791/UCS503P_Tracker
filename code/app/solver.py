# code/app/solver.py
from typing import List
from app.models import Commitment, ScheduleGrid

def place_fixed_events(grid: ScheduleGrid, events: List[Commitment]) -> ScheduleGrid:
    """Pass 1: Places immovable events onto their requested day and slot index."""
    # Create a quick lookup map by (day, slot_index)
    slot_map = {(slot.day, slot.slot_index): slot for slot in grid.slots}

    for event in events:
        key = (event.day, event.slot_index)
        if key in slot_map:
            slot = slot_map[key]
            if slot.occupied_by is not None:
                raise ValueError(f"Conflict: Slot {event.day} index {event.slot_index} is already occupied by '{slot.occupied_by}'.")
            slot.occupied_by = event.title

    return grid
