# code/app/solver.py
from typing import List
from app.models import Commitment, CommitmentType, ScheduleGrid

def place_fixed_events(grid: ScheduleGrid, events: List[Commitment]) -> ScheduleGrid:
    """Pass 1: Places immovable events onto their requested day and slot index."""
    slot_map = {(slot.day, slot.slot_index): slot for slot in grid.slots}
    for event in events:
        if event.day is None or event.slot_index is None:
            raise ValueError(f"Fixed event '{event.title}' must specify both 'day' and 'slot_index'.")
        key = (event.day, event.slot_index)
        if key in slot_map:
            slot = slot_map[key]
            if slot.occupied_by is not None:
                raise ValueError(f"Conflict: Slot {event.day} index {event.slot_index} is already occupied.")
            slot.occupied_by = event.title
    return grid

def place_recurring_quotas(grid: ScheduleGrid, quotas: List[Commitment]) -> ScheduleGrid:
    """Pass 2: Places recurring goals across available days up to their target frequency."""
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    slot_map = {(slot.day, slot.slot_index): slot for slot in grid.slots}

    for quota in quotas:
        placed_count = 0
        preferred_slot = quota.slot_index if quota.slot_index is not None else 0
        target = quota.target_frequency or 1

        for day in days:
            if placed_count >= target:
                break
            
            slot = slot_map.get((day, preferred_slot))
            if slot and slot.occupied_by is None:
                slot.occupied_by = quota.title
                placed_count += 1

        if placed_count < target:
            raise ValueError(f"Could not fulfill quota for '{quota.title}': scheduled {placed_count}/{target}")

    return grid

def place_hard_deadlines(grid: ScheduleGrid, deadlines: List[Commitment]) -> ScheduleGrid:
    """Pass 3: Backwards-schedules dependency blocks prior to a deadline cutoff."""
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_indices = {day: idx for idx, day in enumerate(days)}
    slot_map = {(slot.day, slot.slot_index): slot for slot in grid.slots}

    for task in deadlines:
        needed = task.required_blocks or 1
        placed = 0

        if task.deadline_day is None or task.deadline_slot is None:
            raise ValueError(f"Hard deadline task '{task.title}' must specify both 'deadline_day' and 'deadline_slot'.")
        if task.deadline_day not in day_indices:
            raise ValueError(f"Invalid deadline_day '{task.deadline_day}' for task '{task.title}'.")

        target_day_idx = day_indices[task.deadline_day]
        target_slot = task.deadline_slot - 1

        current_day_idx = target_day_idx
        current_slot = target_slot

        while current_day_idx >= 0 and placed < needed:
            while current_slot >= 0 and placed < needed:
                day_name = days[current_day_idx]
                slot = slot_map.get((day_name, current_slot))
                if slot and slot.occupied_by is None:
                    slot.occupied_by = task.title
                    placed += 1
                current_slot -= 1
            
            current_day_idx -= 1
            current_slot = 11

        if placed < needed:
            raise ValueError(f"Insufficient capacity before deadline for '{task.title}'")

    return grid

def place_flexible_tasks(grid: ScheduleGrid, tasks: List[Commitment]) -> ScheduleGrid:
    """Pass 4: Backfills remaining empty slots with ranked backlog tasks."""
    sorted_tasks = sorted(tasks, key=lambda t: t.priority or 100)
    empty_slots = [slot for slot in grid.slots if slot.occupied_by is None]
    slot_idx = 0

    for task in sorted_tasks:
        needed = task.required_blocks or 1
        placed = 0

        while slot_idx < len(empty_slots) and placed < needed:
            empty_slots[slot_idx].occupied_by = task.title
            placed += 1
            slot_idx += 1

    return grid


def solve_week(commitments: List[Commitment]) -> ScheduleGrid:
    """Orchestrates the 4-pass allocation pipeline on a fresh weekly grid."""
    grid = ScheduleGrid.create_empty_week()

    # Segregate commitments by type
    fixed_events = [c for c in commitments if c.commitment_type == CommitmentType.FIXED_EVENT]
    recurring_quotas = [c for c in commitments if c.commitment_type == CommitmentType.RECURRING_QUOTA]
    hard_deadlines = [c for c in commitments if c.commitment_type == CommitmentType.HARD_DEADLINE]
    flexible_tasks = [c for c in commitments if c.commitment_type == CommitmentType.FLEXIBLE_TASK]

    # Execute passes sequentially
    grid = place_fixed_events(grid, fixed_events)
    grid = place_recurring_quotas(grid, recurring_quotas)
    grid = place_hard_deadlines(grid, hard_deadlines)
    grid = place_flexible_tasks(grid, flexible_tasks)

    return grid
