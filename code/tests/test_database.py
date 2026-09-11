import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.db_models import (
    BlockStatus,
    Commitment,
    ConstraintRule,
    DayOfWeek,
    ExecutionLog,
    RuleType,
    ScheduledBlock,
    Strictness,
)
from app.models import CommitmentType


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_commitment_persists_with_defaults(session):
    commitment = Commitment(title="Gym", type=CommitmentType.RECURRING_QUOTA, target_per_week=4)
    session.add(commitment)
    session.commit()

    fetched = session.query(Commitment).one()
    assert fetched.title == "Gym"
    assert fetched.duration_blocks == 1
    assert fetched.priority == 100


def test_scheduled_block_and_execution_log_relationships(session):
    commitment = Commitment(title="Standup", type=CommitmentType.FIXED_EVENT)
    session.add(commitment)
    session.commit()

    block = ScheduledBlock(
        commitment_id=commitment.id,
        slot_index=0,
        day_of_week=DayOfWeek.MONDAY,
        status=BlockStatus.PLANNED,
    )
    session.add(block)
    session.commit()

    log = ExecutionLog(block_id=block.id, completed=True, notes="Done on time")
    session.add(log)
    session.commit()

    fetched_commitment = session.query(Commitment).one()
    assert len(fetched_commitment.scheduled_blocks) == 1
    assert fetched_commitment.scheduled_blocks[0].execution_logs[0].completed is True


def test_constraint_rule_linked_to_commitment(session):
    commitment = Commitment(title="Deep Work", type=CommitmentType.FLEXIBLE_TASK)
    session.add(commitment)
    session.commit()

    rule = ConstraintRule(
        commitment_id=commitment.id,
        rule_type=RuleType.TIME_OF_DAY_AFFINITY,
        target_slot=2,
        strictness=Strictness.HARD,
    )
    session.add(rule)
    session.commit()

    fetched = session.query(Commitment).one()
    assert len(fetched.constraint_rules) == 1
    assert fetched.constraint_rules[0].strictness == Strictness.HARD
