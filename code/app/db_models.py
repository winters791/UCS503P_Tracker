# code/app/db_models.py
import enum
import uuid
from datetime import UTC, datetime, time

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models import CommitmentType


def _uuid() -> str:
    return str(uuid.uuid4())


class DayOfWeek(str, enum.Enum):
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"


class BlockStatus(str, enum.Enum):
    PLANNED = "PLANNED"
    COMPLETED = "COMPLETED"
    MISSED = "MISSED"
    SKIPPED = "SKIPPED"


class RuleType(str, enum.Enum):
    TIME_OF_DAY_AFFINITY = "TIME_OF_DAY_AFFINITY"
    SEPARATION = "SEPARATION"
    ENERGY_TIERING = "ENERGY_TIERING"


class Strictness(str, enum.Enum):
    HARD = "HARD"
    SOFT = "SOFT"


class Commitment(Base):
    __tablename__ = "commitments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[CommitmentType] = mapped_column(Enum(CommitmentType), nullable=False)
    target_per_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_blocks: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    day: Mapped["DayOfWeek | None"] = mapped_column(Enum(DayOfWeek), nullable=True)
    slot_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    deadline_day: Mapped["DayOfWeek | None"] = mapped_column(Enum(DayOfWeek), nullable=True)
    deadline_slot: Mapped[int | None] = mapped_column(Integer, nullable=True)

    scheduled_blocks: Mapped[list["ScheduledBlock"]] = relationship(
        back_populates="commitment", cascade="all, delete-orphan"
    )
    constraint_rules: Mapped[list["ConstraintRule"]] = relationship(
        back_populates="commitment", cascade="all, delete-orphan"
    )


class ScheduledBlock(Base):
    __tablename__ = "scheduled_blocks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    commitment_id: Mapped[str] = mapped_column(ForeignKey("commitments.id"), nullable=False)
    slot_index: Mapped[int] = mapped_column(Integer, nullable=False)
    day_of_week: Mapped[DayOfWeek] = mapped_column(Enum(DayOfWeek), nullable=False)
    status: Mapped[BlockStatus] = mapped_column(
        Enum(BlockStatus), nullable=False, default=BlockStatus.PLANNED
    )
    actual_start: Mapped[time | None] = mapped_column(Time, nullable=True)

    commitment: Mapped["Commitment"] = relationship(back_populates="scheduled_blocks")
    execution_logs: Mapped[list["ExecutionLog"]] = relationship(
        back_populates="block", cascade="all, delete-orphan"
    )


class ConstraintRule(Base):
    __tablename__ = "constraint_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    commitment_id: Mapped[str] = mapped_column(ForeignKey("commitments.id"), nullable=False)
    rule_type: Mapped[RuleType] = mapped_column(Enum(RuleType), nullable=False)
    target_slot: Mapped[int | None] = mapped_column(Integer, nullable=True)
    strictness: Mapped[Strictness] = mapped_column(
        Enum(Strictness), nullable=False, default=Strictness.SOFT
    )

    commitment: Mapped["Commitment"] = relationship(back_populates="constraint_rules")


class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    block_id: Mapped[str] = mapped_column(ForeignKey("scheduled_blocks.id"), nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    logged_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )

    block: Mapped["ScheduledBlock"] = relationship(back_populates="execution_logs")
