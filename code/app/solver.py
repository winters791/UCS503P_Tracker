# code/app/solver.py
"""Four-pass weekly scheduler with constraint rules.

Rules attached to a commitment narrow where its blocks may go:

  TIME_OF_DAY_AFFINITY  target_slot is a time band - 0 morning (08:00-11:50),
                        1 afternoon (12:00-15:50), 2 evening (16:00-19:50).
  ENERGY_TIERING        high-focus work: only slots up to and including
                        target_slot (default 3, i.e. before noon), taking the
                        earliest hours across the week first.
  SEPARATION            recurring quotas only: at least target_slot rest days
                        between sessions (1 = never on consecutive days).

A HARD rule is never broken - if it cannot be met the commitment fails like
any other capacity problem. A SOFT rule is tried first and then relaxed for
whatever did not fit, with a warning on the grid saying so. A commitment with
no rules is placed exactly as before rules existed.

Cells already occupied by a commitment's own title count towards it: when the
grid comes pre-filled from the database, a block the user has already logged
is part of this week's quota, not something to schedule on top of.
"""
from typing import Callable, List, Optional

from app.models import Commitment, CommitmentType, RuleType, ScheduleGrid, SchedulingRule, TimeSlot

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAY_INDEX = {day: idx for idx, day in enumerate(DAYS)}
SLOTS_PER_DAY = 12
ALL_SLOTS = frozenset(range(SLOTS_PER_DAY))
TIME_BANDS = {0: range(0, 4), 1: range(4, 8), 2: range(8, 12)}
BAND_NAMES = {0: "morning", 1: "afternoon", 2: "evening"}
DEFAULT_ENERGY_CUTOFF = 3


def _allowed_slots(rules: List[SchedulingRule]) -> frozenset:
    """Slot indices (within a day) that satisfy every window rule."""
    allowed = set(ALL_SLOTS)
    for rule in rules:
        if rule.rule_type == RuleType.TIME_OF_DAY_AFFINITY:
            if rule.target_slot not in TIME_BANDS:
                raise ValueError(f"Time-of-day rule needs a band 0-2, got {rule.target_slot}")
            allowed &= set(TIME_BANDS[rule.target_slot])
        elif rule.rule_type == RuleType.ENERGY_TIERING:
            cutoff = DEFAULT_ENERGY_CUTOFF if rule.target_slot is None else rule.target_slot
            allowed &= set(range(0, cutoff + 1))
    return frozenset(allowed)


def _earliest_first(rules: List[SchedulingRule]) -> bool:
    return any(r.rule_type == RuleType.ENERGY_TIERING for r in rules)


def _rest_days(rules: List[SchedulingRule]) -> int:
    return max(
        (r.target_slot or 0 for r in rules if r.rule_type == RuleType.SEPARATION),
        default=0,
    )


def _describe(rules: List[SchedulingRule]) -> str:
    parts = []
    for r in rules:
        if r.rule_type == RuleType.TIME_OF_DAY_AFFINITY:
            parts.append(f"{BAND_NAMES.get(r.target_slot, '?')} only")
        elif r.rule_type == RuleType.ENERGY_TIERING:
            cutoff = DEFAULT_ENERGY_CUTOFF if r.target_slot is None else r.target_slot
            parts.append(f"high-focus before slot {cutoff + 1}")
        elif r.rule_type == RuleType.SEPARATION:
            parts.append(f"{r.target_slot or 0} rest day(s) between sessions")
    return ", ".join(parts)


def _place_with_rules(
    grid: ScheduleGrid,
    item: Commitment,
    needed: int,
    place: Callable[[List[SchedulingRule], int], int],
) -> int:
    """Runs place(rules, remaining) with every rule, then - if that fell short
    and some rules were SOFT - again with only the HARD ones. Returns the
    number of blocks placed in total."""
    placed = place(item.rules, needed)
    hard = [r for r in item.rules if r.hard]
    if placed < needed and len(hard) < len(item.rules):
        relaxed = place(hard, needed - placed)
        if relaxed:
            soft = [r for r in item.rules if not r.hard]
            grid.warnings.append(
                f"'{item.title}': {relaxed} block(s) placed outside its soft rule(s) ({_describe(soft)})"
            )
        placed += relaxed
    return placed


def _already_placed(grid: ScheduleGrid, item: Commitment) -> int:
    return sum(1 for s in grid.slots if s.occupied_by == item.title)


def _hard_rule_suffix(item: Commitment) -> str:
    hard = [r for r in item.rules if r.hard]
    return f" under hard rule(s): {_describe(hard)}" if hard else ""


def place_fixed_events(grid: ScheduleGrid, events: List[Commitment]) -> ScheduleGrid:
    """Pass 1: Places immovable events onto their requested day and slot index.
    Rules do not apply - a fixed event already names its exact slot."""
    slot_map = {(slot.day, slot.slot_index): slot for slot in grid.slots}
    for event in events:
        if event.day is None or event.slot_index is None:
            raise ValueError(f"Fixed event '{event.title}' must specify both 'day' and 'slot_index'.")
        key = (event.day, event.slot_index)
        if key in slot_map:
            slot = slot_map[key]
            if slot.occupied_by == event.title:
                continue  # already on the grid
            if slot.occupied_by is not None:
                raise ValueError(f"Conflict: Slot {event.day} index {event.slot_index} is already occupied.")
            slot.occupied_by = event.title
    return grid


def place_recurring_quotas(grid: ScheduleGrid, quotas: List[Commitment]) -> ScheduleGrid:
    """Pass 2: Places recurring goals across available days up to their target
    frequency - one session per day, at the preferred slot or, when a window
    rule applies, at the nearest open slot inside the window."""
    slot_map = {(slot.day, slot.slot_index): slot for slot in grid.slots}

    for quota in quotas:
        preferred = quota.slot_index if quota.slot_index is not None else 0
        target = quota.target_frequency or 1
        session_days = [DAY_INDEX[s.day] for s in grid.slots if s.occupied_by == quota.title]

        def place(rules: List[SchedulingRule], remaining: int) -> int:
            window = _allowed_slots(rules)
            rest = _rest_days(rules)
            if window == ALL_SLOTS:
                candidates = [preferred]
            elif _earliest_first(rules):
                candidates = sorted(window)
            else:
                candidates = sorted(window, key=lambda s: (abs(s - preferred), s))

            placed = 0
            for day_idx, day in enumerate(DAYS):
                if placed >= remaining:
                    break
                # rest=0 still rules out a second session on the same day
                if any(abs(day_idx - d) <= rest for d in session_days):
                    continue
                for slot_index in candidates:
                    slot = slot_map.get((day, slot_index))
                    if slot and slot.occupied_by is None:
                        slot.occupied_by = quota.title
                        session_days.append(day_idx)
                        placed += 1
                        break
            return placed

        if len(session_days) < target:
            _place_with_rules(grid, quota, target - len(session_days), place)
        if len(session_days) < target:
            raise ValueError(
                f"Could not fulfill quota for '{quota.title}': scheduled {len(session_days)}/{target}"
                + _hard_rule_suffix(quota)
            )

    return grid


def place_hard_deadlines(grid: ScheduleGrid, deadlines: List[Commitment]) -> ScheduleGrid:
    """Pass 3: Backwards-schedules dependency blocks prior to a deadline cutoff."""
    slot_map = {(slot.day, slot.slot_index): slot for slot in grid.slots}

    for task in deadlines:
        needed = task.required_blocks or 1

        if task.deadline_day is None or task.deadline_slot is None:
            raise ValueError(f"Hard deadline task '{task.title}' must specify both 'deadline_day' and 'deadline_slot'.")
        if task.deadline_day not in DAY_INDEX:
            raise ValueError(f"Invalid deadline_day '{task.deadline_day}' for task '{task.title}'.")

        deadline_day = DAY_INDEX[task.deadline_day]
        # Every cell strictly before the cutoff, latest first.
        backwards = [
            (day_idx, slot_index)
            for day_idx in range(deadline_day, -1, -1)
            for slot_index in range(SLOTS_PER_DAY - 1, -1, -1)
            if day_idx < deadline_day or slot_index < task.deadline_slot
        ]

        def place(rules: List[SchedulingRule], remaining: int) -> int:
            window = _allowed_slots(rules)
            placed = 0
            for day_idx, slot_index in backwards:
                if placed >= remaining:
                    break
                if slot_index not in window:
                    continue
                slot = slot_map[(DAYS[day_idx], slot_index)]
                if slot.occupied_by is None:
                    slot.occupied_by = task.title
                    placed += 1
            return placed

        placed = _already_placed(grid, task)
        if placed < needed:
            placed += _place_with_rules(grid, task, needed - placed, place)
        if placed < needed:
            raise ValueError(
                f"Insufficient capacity before deadline for '{task.title}'" + _hard_rule_suffix(task)
            )

    return grid


def place_flexible_tasks(grid: ScheduleGrid, tasks: List[Commitment]) -> ScheduleGrid:
    """Pass 4: Backfills remaining empty slots with ranked backlog tasks.
    A task that does not fully fit is reported in grid.warnings rather than
    failing the whole week - it is backlog, not an obligation."""
    sorted_tasks = sorted(tasks, key=lambda t: t.priority or 100)
    slot_major = sorted(grid.slots, key=lambda s: (s.slot_index, DAY_INDEX.get(s.day, 0)))

    for task in sorted_tasks:
        needed = task.required_blocks or 1

        def place(rules: List[SchedulingRule], remaining: int) -> int:
            window = _allowed_slots(rules)
            order: List[TimeSlot] = slot_major if _earliest_first(rules) else grid.slots
            placed = 0
            for slot in order:
                if placed >= remaining:
                    break
                if slot.occupied_by is None and slot.slot_index in window:
                    slot.occupied_by = task.title
                    placed += 1
            return placed

        placed = _already_placed(grid, task)
        if placed < needed:
            placed += _place_with_rules(grid, task, needed - placed, place)
        if placed < needed:
            grid.warnings.append(
                f"'{task.title}': only {placed}/{needed} block(s) fit" + _hard_rule_suffix(task)
            )

    return grid


def solve_week(commitments: List[Commitment], grid: Optional[ScheduleGrid] = None) -> ScheduleGrid:
    """Orchestrates the 4-pass allocation pipeline, on a fresh weekly grid
    unless one already holding kept blocks is passed in."""
    grid = grid or ScheduleGrid.create_empty_week()

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
