# code/app/models.py
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class CommitmentType(str, Enum):
    FIXED_EVENT = "FIXED_EVENT"
    RECURRING_QUOTA = "RECURRING_QUOTA"
    FLEXIBLE_TASK = "FLEXIBLE_TASK"
    HARD_DEADLINE = "HARD_DEADLINE"

class RuleType(str, Enum):
    TIME_OF_DAY_AFFINITY = "TIME_OF_DAY_AFFINITY"
    SEPARATION = "SEPARATION"
    ENERGY_TIERING = "ENERGY_TIERING"

class SchedulingRule(BaseModel):
    """Solver-side view of a ConstraintRule. What target_slot means depends on
    the kind - see the rule helpers in solver.py."""
    rule_type: RuleType
    target_slot: Optional[int] = None
    hard: bool = False

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
    rules: List[SchedulingRule] = Field(default_factory=list)

class TimeSlot(BaseModel):
    day: str
    slot_index: int
    occupied_by: Optional[str] = None

class ScheduleGrid(BaseModel):
    slots: List[TimeSlot] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    @classmethod
    def create_empty_week(cls) -> "ScheduleGrid":
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        all_slots = [
            TimeSlot(day=d, slot_index=i)
            for d in days
            for i in range(12)
        ]
        return cls(slots=all_slots)
