# code/app/routers/constraint_rules.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import db_models, schemas
from app.database import get_db
from app.models import CommitmentType, RuleType
from app.placement import auto_place, has_placement_info, readable_messages
from app.solver import SLOTS_PER_DAY, TIME_BANDS

router = APIRouter(prefix="/constraint-rules", tags=["constraint-rules"])


def _validate(commitment: db_models.Commitment, rule_type: RuleType, target_slot: int | None) -> None:
    """Rejects rules the solver could not interpret - see solver.py for what
    target_slot means for each rule type."""
    if commitment.type == CommitmentType.FIXED_EVENT:
        raise HTTPException(status_code=422, detail="Fixed events have an exact slot; rules do not apply")
    if rule_type == RuleType.TIME_OF_DAY_AFFINITY and target_slot not in TIME_BANDS:
        raise HTTPException(
            status_code=422,
            detail="Time-of-day rule needs target_slot 0 (morning), 1 (afternoon) or 2 (evening)",
        )
    if rule_type == RuleType.ENERGY_TIERING and target_slot is not None and not 0 <= target_slot < SLOTS_PER_DAY:
        raise HTTPException(status_code=422, detail=f"Energy rule cutoff must be a slot 0-{SLOTS_PER_DAY - 1}")
    if rule_type == RuleType.SEPARATION:
        if commitment.type != CommitmentType.RECURRING_QUOTA:
            raise HTTPException(status_code=422, detail="Separation rules apply to recurring quotas only")
        if target_slot is None or not 1 <= target_slot <= 6:
            raise HTTPException(status_code=422, detail="Separation rule needs 1-6 rest days in target_slot")


def _replace_blocks(db: Session, commitment: db_models.Commitment) -> list[str]:
    """Re-runs auto-placement so a rule change shows up on the grid straight
    away. Anything that is not auto-placed (flexible tasks, or a commitment
    still missing its placement fields) keeps its blocks - flexible tasks pick
    up their rules on the next re-slot."""
    db.flush()
    db.expire(commitment, ["constraint_rules"])
    if not has_placement_info(commitment):
        return []
    try:
        return auto_place(db, commitment)
    except ValueError as exc:
        detail = readable_messages(db, [str(exc)])[0]
        db.rollback()
        raise HTTPException(status_code=409, detail=detail) from exc


@router.post("", response_model=schemas.ConstraintRuleWriteResult, status_code=201)
def create_constraint_rule(payload: schemas.ConstraintRuleCreate, db: Session = Depends(get_db)):
    commitment = db.get(db_models.Commitment, payload.commitment_id)
    if commitment is None:
        raise HTTPException(status_code=404, detail="Commitment not found")
    _validate(commitment, payload.rule_type, payload.target_slot)
    rule = db_models.ConstraintRule(**payload.model_dump())
    db.add(rule)
    warnings = _replace_blocks(db, commitment)
    db.commit()
    db.refresh(rule)
    return schemas.ConstraintRuleWriteResult.model_validate(rule).model_copy(update={"warnings": warnings})


@router.get("", response_model=list[schemas.ConstraintRuleRead])
def list_constraint_rules(db: Session = Depends(get_db)):
    return db.query(db_models.ConstraintRule).all()


@router.get("/{rule_id}", response_model=schemas.ConstraintRuleRead)
def get_constraint_rule(rule_id: str, db: Session = Depends(get_db)):
    rule = db.get(db_models.ConstraintRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Constraint rule not found")
    return rule


@router.patch("/{rule_id}", response_model=schemas.ConstraintRuleWriteResult)
def update_constraint_rule(
    rule_id: str, payload: schemas.ConstraintRuleUpdate, db: Session = Depends(get_db)
):
    rule = db.get(db_models.ConstraintRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Constraint rule not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    _validate(rule.commitment, rule.rule_type, rule.target_slot)
    warnings = _replace_blocks(db, rule.commitment)
    db.commit()
    db.refresh(rule)
    return schemas.ConstraintRuleWriteResult.model_validate(rule).model_copy(update={"warnings": warnings})


@router.delete("/{rule_id}", status_code=204)
def delete_constraint_rule(rule_id: str, db: Session = Depends(get_db)):
    rule = db.get(db_models.ConstraintRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Constraint rule not found")
    commitment = rule.commitment
    db.delete(rule)
    _replace_blocks(db, commitment)
    db.commit()
