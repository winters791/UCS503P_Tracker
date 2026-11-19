# code/seed.py
"""Populate the database with a demo week that exercises every feature.

Run from code/ (the SQLite path is relative):
    ../venv/bin/python seed.py            # refuses if data already exists
    ../venv/bin/python seed.py --reset    # wipe and re-seed

The demo week is a 5th-semester student's timetable:
  * FIXED_EVENT      lectures and labs, placed on save
  * RECURRING_QUOTA  gym 4x and morning run 3x - the run skips Tuesday
                     because a lecture already owns that slot
  * HARD_DEADLINE    two submissions, backward-scheduled from their cutoffs
                     and flowing around lectures
  * FLEXIBLE_TASK    a ranked backlog left UNPLACED so the "Re-slot flexible
                     tasks" button has something visible to do
Monday/Tuesday blocks get execution logs, as if today were Wednesday.

Slot index -> start time: 0=08:00 1=09:00 2=10:00 3=11:00 4=12:00 5=13:00
                          6=14:00 7=15:00 8=16:00 9=17:00 10=18:00 11=19:00
"""
import sys

from sqlalchemy import delete

from app import db_models, weeks
from app.database import SessionLocal
from app.db_models import BlockStatus, DayOfWeek as D
from app.models import CommitmentType as T
from app.placement import auto_place

# Ordered like the solver passes: rigid first, so later items flow around them.
COMMITMENTS = [
    # ---- FIXED_EVENT: title, day, slot ----------------------------------
    dict(title="SE Lecture",   type=T.FIXED_EVENT, day=D.MONDAY,    slot_index=1),
    dict(title="DBMS Lecture", type=T.FIXED_EVENT, day=D.MONDAY,    slot_index=3),
    dict(title="OS Lecture",   type=T.FIXED_EVENT, day=D.TUESDAY,   slot_index=0),
    dict(title="SE Lab",       type=T.FIXED_EVENT, day=D.TUESDAY,   slot_index=6),
    dict(title="SE Lab",       type=T.FIXED_EVENT, day=D.TUESDAY,   slot_index=7),
    dict(title="DBMS Lecture", type=T.FIXED_EVENT, day=D.WEDNESDAY, slot_index=2),
    dict(title="CN Lecture",   type=T.FIXED_EVENT, day=D.WEDNESDAY, slot_index=4),
    dict(title="OS Lecture",   type=T.FIXED_EVENT, day=D.THURSDAY,  slot_index=1),
    dict(title="DBMS Lab",     type=T.FIXED_EVENT, day=D.THURSDAY,  slot_index=6),
    dict(title="DBMS Lab",     type=T.FIXED_EVENT, day=D.THURSDAY,  slot_index=7),
    dict(title="SE Lecture",   type=T.FIXED_EVENT, day=D.FRIDAY,    slot_index=3),
    dict(title="CN Lecture",   type=T.FIXED_EVENT, day=D.FRIDAY,    slot_index=5),
    # ---- RECURRING_QUOTA: target/week at a preferred slot ----------------
    dict(title="Gym",         type=T.RECURRING_QUOTA, target_per_week=4, slot_index=9, priority=20),
    dict(title="Morning run", type=T.RECURRING_QUOTA, target_per_week=3, slot_index=0, priority=30),
    # ---- HARD_DEADLINE: blocks needed before a cutoff --------------------
    dict(title="DBMS assignment", type=T.HARD_DEADLINE, deadline_day=D.WEDNESDAY, deadline_slot=2,
         duration_blocks=3, priority=5),
    dict(title="SE project report", type=T.HARD_DEADLINE, deadline_day=D.FRIDAY, deadline_slot=4,
         duration_blocks=4, priority=10),
    # ---- FLEXIBLE_TASK: ranked backlog, filled by "Re-slot" --------------
    dict(title="DSA practice",       type=T.FLEXIBLE_TASK, priority=10, duration_blocks=5),
    dict(title="CN revision",        type=T.FLEXIBLE_TASK, priority=30, duration_blocks=3),
    dict(title="Read 'Clean Code'",  type=T.FLEXIBLE_TASK, priority=80, duration_blocks=2),
]

# (title, day, slot) -> (completed, note). Pretend it's Wednesday morning.
EXECUTION = {
    ("SE Lecture",   D.MONDAY,  1): (True,  None),
    ("DBMS Lecture", D.MONDAY,  3): (True,  None),
    ("Morning run",  D.MONDAY,  0): (True,  "5 km, felt good"),
    ("Gym",          D.MONDAY,  9): (True,  None),
    ("OS Lecture",   D.TUESDAY, 0): (False, "Overslept"),
    ("SE Lab",       D.TUESDAY, 6): (True,  None),
    ("SE Lab",       D.TUESDAY, 7): (True,  None),
    ("Gym",          D.TUESDAY, 9): (False, "Lab ran late"),
}

DAYS = [d.value for d in D]


def wipe(db):
    for model in (db_models.ExecutionLog, db_models.ScheduledBlock,
                  db_models.ConstraintRule, db_models.Commitment):
        db.execute(delete(model))
    db.flush()


def seed(db):
    for spec in COMMITMENTS:
        c = db_models.Commitment(**spec)
        db.add(c)
        db.flush()
        auto_place(db, c)

    blocks = {
        (b.commitment.title, b.day_of_week, b.slot_index): b
        for b in db.query(db_models.ScheduledBlock).all()
    }
    for key, (completed, note) in EXECUTION.items():
        block = blocks[key]
        block.status = BlockStatus.COMPLETED if completed else BlockStatus.MISSED
        block.status_updated_at = weeks.utc_stamp()
        db.add(db_models.ExecutionLog(block_id=block.id, completed=completed, notes=note))


def print_grid(db):
    cells = {(b.day_of_week.value, b.slot_index): b for b in db.query(db_models.ScheduledBlock).all()}
    mark = {BlockStatus.COMPLETED: "+", BlockStatus.MISSED: "x", BlockStatus.PLANNED: " ", BlockStatus.SKIPPED: "-"}
    col = 17
    print("\n" + " " * 7 + "".join(d[:3].ljust(col) for d in DAYS))
    for s in range(12):
        row = f"{8 + s:02d}:00  "
        for d in DAYS:
            b = cells.get((d, s))
            row += ((mark[b.status] + b.commitment.title[: col - 3]) if b else ".").ljust(col)
        print(row)
    print("\n  + completed   x missed   (blank) planned")


def main():
    reset = "--reset" in sys.argv
    db = SessionLocal()
    try:
        if db.query(db_models.Commitment).count():
            if not reset:
                print("Database already has commitments. Re-run with --reset to replace them.")
                sys.exit(1)
            wipe(db)
        seed(db)
        db.commit()
        n_c = db.query(db_models.Commitment).count()
        n_b = db.query(db_models.ScheduledBlock).count()
        print(f"Seeded {n_c} commitments and {n_b} scheduled blocks.")
        print_grid(db)
        print("\nFlexible tasks (DSA practice, CN revision, Read 'Clean Code') are in the")
        print("sidebar but unplaced - drag any block, then click 'Re-slot flexible tasks'.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
