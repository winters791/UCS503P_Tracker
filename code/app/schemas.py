# code/app/schemas.py
from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.db_models import BlockStatus, DayOfWeek, RuleType, Strictness
from app.models import CommitmentType


class CommitmentBase(BaseModel):
    title: str
    type: CommitmentType
    target_per_week: Optional[int] = None
    duration_blocks: int = 1
    priority: int = 100
    day: Optional[DayOfWeek] = None
    slot_index: Optional[int] = None
    deadline_day: Optional[DayOfWeek] = None
    deadline_slot: Optional[int] = None


class CommitmentCreate(CommitmentBase):
    pass


class CommitmentUpdate(BaseModel):
    title: Optional[str] = None
    type: Optional[CommitmentType] = None
    target_per_week: Optional[int] = None
    duration_blocks: Optional[int] = None
    priority: Optional[int] = None
    day: Optional[DayOfWeek] = None
    slot_index: Optional[int] = None
    deadline_day: Optional[DayOfWeek] = None
    deadline_slot: Optional[int] = None


class CommitmentRead(CommitmentBase):
    model_config = ConfigDict(from_attributes=True)
    id: str


class ScheduledBlockBase(BaseModel):
    commitment_id: str
    slot_index: int
    day_of_week: DayOfWeek
    status: BlockStatus = BlockStatus.PLANNED
    actual_start: Optional[time] = None


class ScheduledBlockCreate(ScheduledBlockBase):
    pass


class ScheduledBlockUpdate(BaseModel):
    slot_index: Optional[int] = None
    day_of_week: Optional[DayOfWeek] = None
    status: Optional[BlockStatus] = None
    actual_start: Optional[time] = None


class ScheduledBlockRead(ScheduledBlockBase):
    model_config = ConfigDict(from_attributes=True)
    id: str


class ConstraintRuleBase(BaseModel):
    commitment_id: str
    rule_type: RuleType
    target_slot: Optional[int] = None
    strictness: Strictness = Strictness.SOFT


class ConstraintRuleCreate(ConstraintRuleBase):
    pass


class ConstraintRuleUpdate(BaseModel):
    rule_type: Optional[RuleType] = None
    target_slot: Optional[int] = None
    strictness: Optional[Strictness] = None


class ConstraintRuleRead(ConstraintRuleBase):
    model_config = ConfigDict(from_attributes=True)
    id: str


class ConstraintRuleWriteResult(ConstraintRuleRead):
    """A saved rule plus anything the re-placement had to compromise on."""
    warnings: list[str] = []


class ExecutionLogBase(BaseModel):
    block_id: str
    completed: bool = False
    notes: Optional[str] = None


class ExecutionLogCreate(ExecutionLogBase):
    pass


class ExecutionLogUpdate(BaseModel):
    completed: Optional[bool] = None
    notes: Optional[str] = None


class ExecutionLogRead(ExecutionLogBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    logged_at: datetime


class ScheduleSlotOut(BaseModel):
    day_of_week: DayOfWeek
    slot_index: int
    block_id: Optional[str] = None
    commitment_id: Optional[str] = None
    commitment_title: Optional[str] = None
    commitment_type: Optional[CommitmentType] = None
    status: Optional[BlockStatus] = None


class ScheduleSolveResult(BaseModel):
    slots: list[ScheduleSlotOut]
    warnings: list[str] = []


class WeekResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    week_start: date
    completed: int
    met: bool


class QuotaConsistencyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    commitment_id: str
    title: str
    target: int
    completed_this_week: int
    streak: int
    history: list[WeekResultOut]


class ConsistencyReport(BaseModel):
    week_start: date
    quotas: list[QuotaConsistencyOut]


class TallyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    planned: int
    completed: int
    missed: int
    not_logged: int
    upcoming: int
    due: int


class CommitmentTallyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    commitment_id: str
    title: str
    type: CommitmentType
    tally: TallyOut


class QuotaResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    title: str
    completed: int
    target: int
    met: bool


class RetrospectiveReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    week_start: date
    week_end: date
    totals: TallyOut
    by_commitment: list[CommitmentTallyOut]
    by_day: list[TallyOut]
    quota_results: list[QuotaResultOut]
    highlights: list[str]
