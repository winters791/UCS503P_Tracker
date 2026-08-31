# code/tests/test_solver.py
from app.models import TimeSlot, CommitmentType

def test_create_empty_slot():
    slot = TimeSlot(day="Monday", slot_index=0)
    assert slot.occupied_by is None
    assert slot.slot_index == 0
    assert slot.day == "Monday"

def test_commitment_types_exist():
    assert CommitmentType.FIXED_EVENT == "FIXED_EVENT"
