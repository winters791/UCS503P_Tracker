# code/app/schemas.py
from datetime import datetime, time
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


class CommitmentCreate(CommitmentBase):
    pass


class CommitmentUpdate(BaseModel):
    title: Optional[str] = None
    type: Optional[CommitmentType] = None
    target_per_week: Optional[int] = None
    duration_blocks: Optional[int] = None
    priority: Optional[int] = None


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
