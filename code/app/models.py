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
    day: Optional[str] = None          # e.g., "Monday"
    slot_index: Optional[int] = None   # 0 to 11 (50-minute discrete blocks)

class TimeSlot(BaseModel):
    day: str
    slot_index: int
    occupied_by: Optional[str] = None

class ScheduleGrid(BaseModel):
    slots: List[TimeSlot] = Field(default_factory=list)

    @classmethod
    def create_empty_week(cls) -> "ScheduleGrid":
        """Creates a blank weekly grid with 7 days and 12 slots (50-min each) per day."""
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        all_slots = [
            TimeSlot(day=d, slot_index=i)
            for d in days
            for i in range(12)
        ]
        return cls(slots=all_slots)
