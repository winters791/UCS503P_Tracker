# code/app/main.py
from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from app.routers import commitments, constraint_rules, execution_logs, schedule, scheduled_blocks

app = FastAPI(title="Ops API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(commitments.router)
app.include_router(scheduled_blocks.router)
app.include_router(constraint_rules.router)
app.include_router(execution_logs.router)
app.include_router(schedule.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
