# code/app/routers/execution_logs.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import db_models, schemas
from app.database import get_db

router = APIRouter(prefix="/execution-logs", tags=["execution-logs"])


@router.post("", response_model=schemas.ExecutionLogRead, status_code=201)
def create_execution_log(payload: schemas.ExecutionLogCreate, db: Session = Depends(get_db)):
    if db.get(db_models.ScheduledBlock, payload.block_id) is None:
        raise HTTPException(status_code=404, detail="Scheduled block not found")
    log = db_models.ExecutionLog(**payload.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("", response_model=list[schemas.ExecutionLogRead])
def list_execution_logs(db: Session = Depends(get_db)):
    return db.query(db_models.ExecutionLog).all()


@router.get("/{log_id}", response_model=schemas.ExecutionLogRead)
def get_execution_log(log_id: str, db: Session = Depends(get_db)):
    log = db.get(db_models.ExecutionLog, log_id)
    if log is None:
        raise HTTPException(status_code=404, detail="Execution log not found")
    return log


@router.patch("/{log_id}", response_model=schemas.ExecutionLogRead)
def update_execution_log(
    log_id: str, payload: schemas.ExecutionLogUpdate, db: Session = Depends(get_db)
):
    log = db.get(db_models.ExecutionLog, log_id)
    if log is None:
        raise HTTPException(status_code=404, detail="Execution log not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(log, field, value)
    db.commit()
    db.refresh(log)
    return log


@router.delete("/{log_id}", status_code=204)
def delete_execution_log(log_id: str, db: Session = Depends(get_db)):
    log = db.get(db_models.ExecutionLog, log_id)
    if log is None:
        raise HTTPException(status_code=404, detail="Execution log not found")
    db.delete(log)
    db.commit()
