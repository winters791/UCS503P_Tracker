# code/app/models.py
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class CommitmentType(str, Enum):
    FIXED_EVENT = "FIXED_EVENT"
    RECURRING_QUOTA = "RECURRING_QUOTA"
    FLEXIBLE_TASK = "FLEXIBLE_TASK"
    HARD_DEADLINE = "HARD_DEADLINE"

class Commitment(BaseModel):
    id: str
    title: str
    commitment_type: CommitmentType
    day: Optional[str] = None          # For FIXED_EVENT (e.g., "Monday")
    slot_index: Optional[int] = None   # Target slot index (0 to 11)
    target_frequency: Optional[int] = None  # For RECURRING_QUOTA (e.g., 3 times/week)
    deadline_day: Optional[str] = None          # For HARD_DEADLINE
    deadline_slot: Optional[int] = None         # Slot index cutoff (0 to 11)
    required_blocks: Optional[int] = 1
    priority: Optional[int] = 100 #lower value = higher priority

class TimeSlot(BaseModel):
    day: str
    slot_index: int
    occupied_by: Optional[str] = None

class ScheduleGrid(BaseModel):
    slots: List[TimeSlot] = Field(default_factory=list)

    @classmethod
    def create_empty_week(cls) -> "ScheduleGrid":
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        all_slots = [
            TimeSlot(day=d, slot_index=i)
            for d in days
            for i in range(12)
        ]
        return cls(slots=all_slots)
