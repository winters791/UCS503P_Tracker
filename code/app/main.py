# code/app/main.py
from fastapi import FastAPI

from app.routers import commitments, constraint_rules, execution_logs, scheduled_blocks

app = FastAPI(title="Ops API", version="0.1.0")

app.include_router(commitments.router)
app.include_router(scheduled_blocks.router)
app.include_router(constraint_rules.router)
app.include_router(execution_logs.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
