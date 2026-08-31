# code/tests/test_solver.py
from app.models import Commitment, CommitmentType, ScheduleGrid
from app.solver import place_fixed_events

def test_place_fixed_event_success():
    grid = ScheduleGrid.create_empty_week()
    lecture = Commitment(
        id="c1",
        title="Operating Systems Lecture",
        commitment_type=CommitmentType.FIXED_EVENT,
        day="Monday",
        slot_index=2
    )

    updated_grid = place_fixed_events(grid=grid, events=[lecture])
    
    # Find Monday slot 2 and verify it is occupied
    target_slot = next(s for s in updated_grid.slots if s.day == "Monday" and s.slot_index == 2)
    assert target_slot.occupied_by == "Operating Systems Lecture"
