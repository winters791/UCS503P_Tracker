import pytest
from app.models import Commitment, CommitmentType, ScheduleGrid
from app.solver import place_flexible_tasks, place_hard_deadlines, place_fixed_events
from app.solver import solve_week

def test_place_flexible_tasks_priority():
    grid = ScheduleGrid.create_empty_week()

    # High priority task (priority 1, requires 2 blocks)
    dsa = Commitment(
        id="f1",
        title="DSA Practice",
        commitment_type=CommitmentType.FLEXIBLE_TASK,
        priority=1,
        required_blocks=2
    )

    # Lower priority task (priority 2, requires 1 block)
    reading = Commitment(
        id="f2",
        title="Deep Reading",
        commitment_type=CommitmentType.FLEXIBLE_TASK,
        priority=2,
        required_blocks=1
    )

    updated_grid = place_flexible_tasks(grid=grid, tasks=[reading, dsa])

    # Verification: High priority task fills Monday slot 0 and 1
    mon_0 = next(s for s in updated_grid.slots if s.day == "Monday" and s.slot_index == 0)
    mon_1 = next(s for s in updated_grid.slots if s.day == "Monday" and s.slot_index == 1)
    mon_2 = next(s for s in updated_grid.slots if s.day == "Monday" and s.slot_index == 2)

    assert mon_0.occupied_by == "DSA Practice"
    assert mon_1.occupied_by == "DSA Practice"
    assert mon_2.occupied_by == "Deep Reading"

def test_place_hard_deadlines_backwards():
    grid = ScheduleGrid.create_empty_week()
    task = Commitment(
        id="h1",
        title="Project Submission",
        commitment_type=CommitmentType.HARD_DEADLINE,
        deadline_day="Tuesday",
        deadline_slot=2,
        required_blocks=3
    )

    updated_grid = place_hard_deadlines(grid=grid, deadlines=[task])

    # Should place backwards from Tuesday slot 1 -> Tuesday slot 0 -> Monday slot 11
    tue_1 = next(s for s in updated_grid.slots if s.day == "Tuesday" and s.slot_index == 1)
    tue_0 = next(s for s in updated_grid.slots if s.day == "Tuesday" and s.slot_index == 0)
    mon_11 = next(s for s in updated_grid.slots if s.day == "Monday" and s.slot_index == 11)

    assert tue_1.occupied_by == "Project Submission"
    assert tue_0.occupied_by == "Project Submission"
    assert mon_11.occupied_by == "Project Submission"

def test_place_hard_deadlines_validation():
    grid = ScheduleGrid.create_empty_week()
    task = Commitment(
        id="h2",
        title="Incomplete Task",
        commitment_type=CommitmentType.HARD_DEADLINE,
        deadline_day=None,
        deadline_slot=None
    )

    with pytest.raises(ValueError, match="must specify both 'deadline_day' and 'deadline_slot'"):
        place_hard_deadlines(grid=grid, deadlines=[task])

def test_full_pipeline_solve_week():
    commitments = [
        # Pass 1: Immovable event on Monday slot 0
        Commitment(
            id="1",
            title="Standup Meeting",
            commitment_type=CommitmentType.FIXED_EVENT,
            day="Monday",
            slot_index=0
        ),
        # Pass 2: Gym 2x this week preferring slot 1
        Commitment(
            id="2",
            title="Gym",
            commitment_type=CommitmentType.RECURRING_QUOTA,
            slot_index=1,
            target_frequency=2
        ),
        # Pass 3: Assignment due Tuesday slot 2, needs 1 prep block
        Commitment(
            id="3",
            title="Lab Submission Prep",
            commitment_type=CommitmentType.HARD_DEADLINE,
            deadline_day="Tuesday",
            deadline_slot=2,
            required_blocks=1
        ),
        # Pass 4: Flexible reading task
        Commitment(
            id="4",
            title="Elective Reading",
            commitment_type=CommitmentType.FLEXIBLE_TASK,
            priority=1,
            required_blocks=1
        ),
    ]

    grid = solve_week(commitments)

    # 1. Monday slot 0 must have the fixed meeting
    mon_0 = next(s for s in grid.slots if s.day == "Monday" and s.slot_index == 0)
    assert mon_0.occupied_by == "Standup Meeting"

    # 2. Gym must be placed twice
    gym_slots = [s for s in grid.slots if s.occupied_by == "Gym"]
    assert len(gym_slots) == 2

    # 3. Lab prep must be scheduled right before Tuesday slot 2 (Tuesday slot 1 or Monday)
    lab_slot = next(s for s in grid.slots if s.occupied_by == "Lab Submission Prep")
    assert lab_slot is not None

    # 4. Reading must take the next available open slot
    reading_slot = next(s for s in grid.slots if s.occupied_by == "Elective Reading")
    assert reading_slot is not None
