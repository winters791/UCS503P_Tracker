# code/app/routers/constraint_rules.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import db_models, schemas
from app.database import get_db

router = APIRouter(prefix="/constraint-rules", tags=["constraint-rules"])


@router.post("", response_model=schemas.ConstraintRuleRead, status_code=201)
def create_constraint_rule(payload: schemas.ConstraintRuleCreate, db: Session = Depends(get_db)):
    if db.get(db_models.Commitment, payload.commitment_id) is None:
        raise HTTPException(status_code=404, detail="Commitment not found")
    rule = db_models.ConstraintRule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.get("", response_model=list[schemas.ConstraintRuleRead])
def list_constraint_rules(db: Session = Depends(get_db)):
    return db.query(db_models.ConstraintRule).all()


@router.get("/{rule_id}", response_model=schemas.ConstraintRuleRead)
def get_constraint_rule(rule_id: str, db: Session = Depends(get_db)):
    rule = db.get(db_models.ConstraintRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Constraint rule not found")
    return rule


@router.patch("/{rule_id}", response_model=schemas.ConstraintRuleRead)
def update_constraint_rule(
    rule_id: str, payload: schemas.ConstraintRuleUpdate, db: Session = Depends(get_db)
):
    rule = db.get(db_models.ConstraintRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Constraint rule not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=204)
def delete_constraint_rule(rule_id: str, db: Session = Depends(get_db)):
    rule = db.get(db_models.ConstraintRule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Constraint rule not found")
    db.delete(rule)
    db.commit()
