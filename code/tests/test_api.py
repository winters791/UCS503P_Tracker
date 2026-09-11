import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestSessionLocal = sessionmaker(bind=engine)

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_commitment_crud_flow(client):
    create_response = client.post(
        "/commitments",
        json={"title": "Gym", "type": "RECURRING_QUOTA", "target_per_week": 4},
    )
    assert create_response.status_code == 201
    commitment = create_response.json()
    assert commitment["title"] == "Gym"
    commitment_id = commitment["id"]

    get_response = client.get(f"/commitments/{commitment_id}")
    assert get_response.status_code == 200

    list_response = client.get("/commitments")
    assert len(list_response.json()) == 1

    patch_response = client.patch(f"/commitments/{commitment_id}", json={"priority": 5})
    assert patch_response.status_code == 200
    assert patch_response.json()["priority"] == 5

    delete_response = client.delete(f"/commitments/{commitment_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/commitments/{commitment_id}")
    assert missing_response.status_code == 404


def test_commitment_not_found_returns_404(client):
    response = client.get("/commitments/does-not-exist")
    assert response.status_code == 404


def test_scheduled_block_requires_existing_commitment(client):
    response = client.post(
        "/scheduled-blocks",
        json={"commitment_id": "does-not-exist", "slot_index": 0, "day_of_week": "Monday"},
    )
    assert response.status_code == 404


def test_constraint_rule_requires_existing_commitment(client):
    response = client.post(
        "/constraint-rules",
        json={"commitment_id": "does-not-exist", "rule_type": "SEPARATION"},
    )
    assert response.status_code == 404


def test_execution_log_requires_existing_block(client):
    response = client.post(
        "/execution-logs",
        json={"block_id": "does-not-exist", "completed": True},
    )
    assert response.status_code == 404


def test_full_entity_chain(client):
    commitment_id = client.post(
        "/commitments", json={"title": "Standup", "type": "FIXED_EVENT"}
    ).json()["id"]

    block_response = client.post(
        "/scheduled-blocks",
        json={"commitment_id": commitment_id, "slot_index": 0, "day_of_week": "Monday"},
    )
    assert block_response.status_code == 201
    block_id = block_response.json()["id"]

    rule_response = client.post(
        "/constraint-rules",
        json={
            "commitment_id": commitment_id,
            "rule_type": "TIME_OF_DAY_AFFINITY",
            "target_slot": 0,
        },
    )
    assert rule_response.status_code == 201

    log_response = client.post(
        "/execution-logs",
        json={"block_id": block_id, "completed": True, "notes": "done"},
    )
    assert log_response.status_code == 201
    assert log_response.json()["completed"] is True

    update_block_response = client.patch(
        f"/scheduled-blocks/{block_id}", json={"status": "COMPLETED"}
    )
    assert update_block_response.status_code == 200
    assert update_block_response.json()["status"] == "COMPLETED"
