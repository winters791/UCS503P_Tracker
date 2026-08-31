# code/app/models.py
from enum import Enum
from typing import Optional
from pydantic import BaseModel

class CommitmentType(str, Enum):
    FIXED_EVENT = "FIXED_EVENT"
    RECURRING_QUOTA = "RECURRING_QUOTA"
    FLEXIBLE_TASK = "FLEXIBLE_TASK"
    HARD_DEADLINE = "HARD_DEADLINE"

class TimeSlot(BaseModel):
    day: str          # e.g., "Monday"
    slot_index: int   # 0 to 11 (representing 50-minute blocks in a day)
    occupied_by: Optional[str] = None
