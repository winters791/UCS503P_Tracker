# code/app/routers/scheduled_blocks.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import db_models, schemas, weeks
from app.database import get_db

router = APIRouter(prefix="/scheduled-blocks", tags=["scheduled-blocks"])


def _stamp_status(block: db_models.ScheduledBlock) -> None:
    """A status counts for the week it is set in - see weeks.py."""
    block.status_updated_at = None if block.status == db_models.BlockStatus.PLANNED else weeks.utc_stamp()


@router.post("", response_model=schemas.ScheduledBlockRead, status_code=201)
def create_scheduled_block(payload: schemas.ScheduledBlockCreate, db: Session = Depends(get_db)):
    if db.get(db_models.Commitment, payload.commitment_id) is None:
        raise HTTPException(status_code=404, detail="Commitment not found")
    block = db_models.ScheduledBlock(**payload.model_dump())
    _stamp_status(block)
    db.add(block)
    db.commit()
    db.refresh(block)
    return block


@router.get("", response_model=list[schemas.ScheduledBlockRead])
def list_scheduled_blocks(db: Session = Depends(get_db)):
    return db.query(db_models.ScheduledBlock).all()


@router.get("/{block_id}", response_model=schemas.ScheduledBlockRead)
def get_scheduled_block(block_id: str, db: Session = Depends(get_db)):
    block = db.get(db_models.ScheduledBlock, block_id)
    if block is None:
        raise HTTPException(status_code=404, detail="Scheduled block not found")
    return block


@router.patch("/{block_id}", response_model=schemas.ScheduledBlockRead)
def update_scheduled_block(
    block_id: str, payload: schemas.ScheduledBlockUpdate, db: Session = Depends(get_db)
):
    block = db.get(db_models.ScheduledBlock, block_id)
    if block is None:
        raise HTTPException(status_code=404, detail="Scheduled block not found")
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(block, field, value)
    if "status" in changes:
        _stamp_status(block)
    db.commit()
    db.refresh(block)
    return block


@router.delete("/{block_id}", status_code=204)
def delete_scheduled_block(block_id: str, db: Session = Depends(get_db)):
    block = db.get(db_models.ScheduledBlock, block_id)
    if block is None:
        raise HTTPException(status_code=404, detail="Scheduled block not found")
    db.delete(block)
    db.commit()
