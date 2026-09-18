# code/app/routers/commitments.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import db_models, schemas
from app.database import get_db
from app.placement import PLACEMENT_FIELDS, auto_place, clear_planned_blocks

router = APIRouter(prefix="/commitments", tags=["commitments"])


@router.post("", response_model=schemas.CommitmentRead, status_code=201)
def create_commitment(payload: schemas.CommitmentCreate, db: Session = Depends(get_db)):
    commitment = db_models.Commitment(**payload.model_dump())
    db.add(commitment)
    db.flush()
    try:
        auto_place(db, commitment)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    db.commit()
    db.refresh(commitment)
    return commitment


@router.get("", response_model=list[schemas.CommitmentRead])
def list_commitments(db: Session = Depends(get_db)):
    return db.query(db_models.Commitment).all()


@router.get("/{commitment_id}", response_model=schemas.CommitmentRead)
def get_commitment(commitment_id: str, db: Session = Depends(get_db)):
    commitment = db.get(db_models.Commitment, commitment_id)
    if commitment is None:
        raise HTTPException(status_code=404, detail="Commitment not found")
    return commitment


@router.patch("/{commitment_id}", response_model=schemas.CommitmentRead)
def update_commitment(
    commitment_id: str, payload: schemas.CommitmentUpdate, db: Session = Depends(get_db)
):
    commitment = db.get(db_models.Commitment, commitment_id)
    if commitment is None:
        raise HTTPException(status_code=404, detail="Commitment not found")
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(commitment, field, value)
    db.flush()
    # Only re-place when something that affects placement changed - a title
    # edit must not move blocks the user has dragged into position.
    if PLACEMENT_FIELDS & changes.keys():
        clear_planned_blocks(db, commitment)
        try:
            auto_place(db, commitment)
        except ValueError as exc:
            db.rollback()
            raise HTTPException(status_code=409, detail=str(exc)) from exc
    db.commit()
    db.refresh(commitment)
    return commitment


@router.delete("/{commitment_id}", status_code=204)
def delete_commitment(commitment_id: str, db: Session = Depends(get_db)):
    commitment = db.get(db_models.Commitment, commitment_id)
    if commitment is None:
        raise HTTPException(status_code=404, detail="Commitment not found")
    db.delete(commitment)
    db.commit()
