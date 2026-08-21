# Ops — Personal Life-Systems Engine & Rules-Driven Scheduler

> **A deterministic, constraint-based weekly life-operating engine.**  
> Moving beyond passive to-do lists to model real-world commitments, fixed routines, flexible focus blocks, and forgiving consistency metrics.

---

## 1. Overview & Core Philosophy

Most productivity and task-management tools fail because they treat human attention as an infinite list of atomic checkboxes. In practice, attention operates on time-bounded blocks, fixed obligations, recurring physical demands, and variable cognitive energy.

**Ops** is a single-user, rules-driven life-operating engine designed around:
1. **Time-Blocked Reality**: Everything lives in discrete **50-minute focus blocks** with built-in transition buffers.
2. **Deterministic Constraint Scheduling**: Automatic placement of flexible work into available schedule slots using a custom constraint solver rather than vague manual dragging.
3. **Weekly Volume Over Rigid Perfectionism**: Consistency metrics that track rolling weekly target quotas (e.g., hit 4/4 gym sessions or 6/7 nutrition targets) rather than fragile all-or-nothing daily chains.
4. **Automated Weekly Retrospectives**: Zero-friction end-of-week reviews analyzing planned vs. executed blocks, missed patterns, and scheduling drift.

---

## 2. System Architecture

```
                    +------------------------------------------+
                    |             React Frontend               |
                    |  - 50-min Grid Canvas (dnd-kit)          |
                    |  - Weekly Horizon & Review Dashboard     |
                    +--------------------+---------------------+
                                         |
                                         | HTTP / JSON REST APIs
                                         v
+-------------------------------------------------------------------------------+
|                             FastAPI Backend                                  |
|                                                                               |
|   +-----------------------+   +-------------------+   +--------------------+  |
|   |  Task & Block Router  |   |  Constraint-Based |   |  Rolling Weekly    |  |
|   |  - Fixed vs Recurring |   |  Scheduler Engine |   |  Review & Metric   |  |
|   |  - One-off Deadlines  |   |  (Python Solver)  |   |  Aggregator        |  |
|   +-----------+-----------+   +---------+---------+   +---------+----------+  |
|               |                         |                       |             |
+---------------+-------------------------+-----------------------+-------------+
                                          |
                                          v (SQLAlchemy ORM)
                    +------------------------------------------+
                    |        PostgreSQL / SQLite Database      |
                    |  - Blocks & Commitments                  |
                    |  - Constraints & Preference Weights      |
                    |  - Execution Logs & Weekly Snapshots     |
                    +------------------------------------------+
```

---

## 3. Data & Entity Model

```
       +--------------------+                 +--------------------+
       |     Commitment     | 1             * |  ScheduledBlock    |
       |--------------------|-----------------|--------------------|
       | id: UUID (PK)      |                 | id: UUID (PK)      |
       | title: VARCHAR     |                 | commitment_id: FK  |
       | type: ENUM         |                 | slot_index: INT    |
       | target_per_week:INT|                 | day_of_week: ENUM  |
       | duration_blocks:INT|                 | status: ENUM       |
       | priority: INT      |                 | actual_start: TIME |
       +--------------------+                 +--------------------+
                 | 1                                     | 1
                 |                                       |
                 | *                                     | *
       +--------------------+                 +--------------------+
       |  ConstraintRule    |                 |   ExecutionLog     |
       |--------------------|                 |--------------------|
       | id: UUID (PK)      |                 | id: UUID (PK)      |
       | commitment_id: FK  |                 | block_id: FK       |
       | rule_type: ENUM    |                 | completed: BOOL    |
       | target_slot: INT   |                 | notes: TEXT        |
       | strictness: ENUM   |                 | logged_at: TIMESTAMP|
       +--------------------+                 +--------------------+
```

### Commitment Types
* `FIXED_EVENT`: Immovable constraints (Lectures, Labs, Exams, Scheduled Appointments).
* `RECURRING_QUOTA`: High-priority recurring sessions with weekly frequency quotas (e.g., Gym 4x/week, Meditations).
* `FLEXIBLE_TASK`: Ranked backlog tasks to auto-fill vacant capacity (DSA practice, project milestones, deep reading).
* `HARD_DEADLINE`: Time-sensitive deliverables requiring backwards-scheduled dependency blocks.

---

## 4. Scheduling Logic & Constraint Solver

The scheduling engine is implemented as a pure Python module with no heavy external solver dependencies. It executes a deterministic, multi-pass slot allocation algorithm:

```python
def generate_weekly_schedule(
    week_grid: ScheduleGrid, 
    commitments: list[Commitment], 
    rules: list[ConstraintRule]
) -> ScheduleResult:
    """
    Pass 1: Place all hard FIXED_EVENT items onto immutable grid coordinates.
    Pass 2: Evaluate RECURRING_QUOTA items with explicit day/time preferences 
            (e.g., Evening gym, minimum 24h rest windows).
    Pass 3: Backtrack-schedule HARD_DEADLINE tasks backwards from due dates.
    Pass 4: Optimize and fill remaining open 50-minute blocks with FLEXIBLE_TASK 
            items sorted by (Priority * Urgency / Remaining_Capacity).
    """
    ...
```

### Constraint Classes Supported:
* **Time-of-Day Affinity**: Restrict items to morning, afternoon, or evening blocks.
* **Separation Rules**: Enforce minimum rest or buffer spacing between specific recurring types.
* **Energy Tiering**: Reserve early-day high-focus slots for high-friction cognitive work.

---

## 5. Non-Punitive Consistency & Rolling Streaks

Traditional habit trackers break streaks upon a single missed calendar day, causing artificial demoralization. **Ops** implements rolling aggregate compliance:

$$\text{Weekly Compliance Rate} = \frac{\text{Completed Sessions in Cycle}}{\text{Target Frequency Quota}} \times 100\%$$

* A streak increments on successful week-boundary transitions if:
  $$\text{Weekly Compliance Rate} \ge 1.0$$
* A skipped session mid-week simply converts remaining unallocated blocks into potential recovery buffers.
* Streaks only decay if the entire weekly window closes below the target quota threshold.

---

## 6. Engineering Scope & 3-Month Execution Roadmap

Ops sits in the sweet spot for an engineering project: straightforward CRUD operations on the surface, with substantive algorithmic depth in the constraint-slotting engine and high front-end polish required for canvas manipulation.

```
+-----------------------------------------------------------------------------+
| Month 1: Data Contracts & Core Constraint Engine                           |
| - Fast-path SQLite schema setup via SQLAlchemy + Alembic                    |
| - Standalone Python scheduling module with exhaustive pytest test suites   |
| - REST API scaffolding (Commitments, Slots, Rules, Execution Logs)          |
+-----------------------------------------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------+
| Month 2: Interactive Grid Canvas & Solver Integration                       |
| - React 50-minute block timeline layout with dnd-kit drag-and-drop          |
| - Bi-directional state syncing: manual overrides trigger re-slotting engine|
| - Real-time slot collision detection and conflict visualizers               |
+-----------------------------------------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------+
| Month 3: Rolling Metrics, Retrospective Engine & Polish                     |
| - Weekly review generator: planned vs. executed delta analysis              |
| - Streak resilience calculators & historic pattern aggregations             |
| - End-to-end local deployment via Docker Compose                            |
+-----------------------------------------------------------------------------+
```

---

## 7. Explicit Non-Goals

To maintain high development velocity and produce a robust single-user tool within 12 weeks, the following are strictly out of scope:
* Multi-tenant authentication, RBAC, or OAuth integrations.
* Real-time multi-user collaboration and WebSockets.
* Native mobile client builds (responsive web canvas only).
* Integrations with third-party sync APIs (Google Calendar / Notion API syncing deferred to v2).

---

## 8. Tech Stack Summary

| Layer | Technology | Rationale |
| :--- | :--- | :--- |
| **Backend** | Python 3.12 / FastAPI / Pydantic v2 | High developer velocity, native type safety, auto OpenAPI generation |
| **Scheduler** | Pure Python Constraint Module | High interview signal, deterministic testing, zero external lock-in |
| **Database** | SQLite (Dev) / PostgreSQL (Prod) | Robust relational modeling for recurring schedules and logs |
| **ORM & Migrations** | SQLAlchemy 2.0 / Alembic | Clean schema contracts and straightforward relational joins |
| **Frontend** | React 18 / TypeScript / Tailwind CSS | Strict UI typing and modular component architecture |
| **Canvas & Drag** | dnd-kit | Accessible, modular drag-and-drop primitives for time blocks |
| **Containerization**| Docker Compose | Single-command deployment (`docker compose up`) for daily use |

---

## 9. Quickstart (Development)

```bash
# Clone the repository
git clone https://github.com/username/ops.git
cd ops

# Backend Setup
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest tests/ -v
uvicorn app.main:app --reload --port 8000

# Frontend Setup (in a separate terminal)
cd ../frontend
npm install
npm run dev
```
