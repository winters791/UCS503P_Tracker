# code/app/routers/commitments.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import db_models, schemas
from app.database import get_db

router = APIRouter(prefix="/commitments", tags=["commitments"])


@router.post("", response_model=schemas.CommitmentRead, status_code=201)
def create_commitment(payload: schemas.CommitmentCreate, db: Session = Depends(get_db)):
    commitment = db_models.Commitment(**payload.model_dump())
    db.add(commitment)
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
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(commitment, field, value)
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
