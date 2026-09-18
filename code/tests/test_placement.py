"""Auto-placement: saving a commitment with placement info creates blocks."""
from tests.test_api import client  # noqa: F401 - reuse the in-memory client fixture


def _blocks(client, commitment_id):
    return [b for b in client.get("/scheduled-blocks").json() if b["commitment_id"] == commitment_id]


def test_fixed_event_is_placed_on_create(client):
    res = client.post(
        "/commitments",
        json={"title": "DBMS lecture", "type": "FIXED_EVENT", "day": "Monday", "slot_index": 2},
    )
    assert res.status_code == 201
    blocks = _blocks(client, res.json()["id"])
    assert [(b["day_of_week"], b["slot_index"]) for b in blocks] == [("Monday", 2)]
    assert blocks[0]["status"] == "PLANNED"


def test_fixed_event_conflict_returns_409_and_creates_nothing(client):
    client.post("/commitments", json={"title": "A", "type": "FIXED_EVENT", "day": "Monday", "slot_index": 2})
    res = client.post("/commitments", json={"title": "B", "type": "FIXED_EVENT", "day": "Monday", "slot_index": 2})
    assert res.status_code == 409
    assert "already occupied" in res.json()["detail"]
    assert [c["title"] for c in client.get("/commitments").json()] == ["A"]


def test_hard_deadline_is_backward_scheduled(client):
    res = client.post(
        "/commitments",
        json={
            "title": "Report",
            "type": "HARD_DEADLINE",
            "deadline_day": "Wednesday",
            "deadline_slot": 3,
            "duration_blocks": 4,
        },
    )
    assert res.status_code == 201
    cells = sorted((b["day_of_week"], b["slot_index"]) for b in _blocks(client, res.json()["id"]))
    # 3 blocks fit before slot 3 on Wednesday (0,1,2); the 4th spills back to Tuesday's last slot.
    assert cells == [("Tuesday", 11), ("Wednesday", 0), ("Wednesday", 1), ("Wednesday", 2)]


def test_recurring_quota_is_spread_across_days(client):
    res = client.post(
        "/commitments",
        json={"title": "Gym", "type": "RECURRING_QUOTA", "target_per_week": 3, "slot_index": 10},
    )
    assert res.status_code == 201
    cells = [(b["day_of_week"], b["slot_index"]) for b in _blocks(client, res.json()["id"])]
    assert cells == [("Monday", 10), ("Tuesday", 10), ("Wednesday", 10)]


def test_flexible_task_is_not_auto_placed(client):
    res = client.post("/commitments", json={"title": "DSA", "type": "FLEXIBLE_TASK"})
    assert res.status_code == 201
    assert _blocks(client, res.json()["id"]) == []


def test_fixed_event_without_slot_is_created_but_not_placed(client):
    res = client.post("/commitments", json={"title": "TBD", "type": "FIXED_EVENT"})
    assert res.status_code == 201
    assert _blocks(client, res.json()["id"]) == []


def test_update_moves_block_when_placement_changes_but_not_on_title_edit(client):
    cid = client.post(
        "/commitments",
        json={"title": "Lab", "type": "FIXED_EVENT", "day": "Monday", "slot_index": 2},
    ).json()["id"]
    block_id = _blocks(client, cid)[0]["id"]

    # Title-only edit keeps the same block untouched.
    client.patch(f"/commitments/{cid}", json={"title": "Lab (renamed)"})
    assert _blocks(client, cid)[0]["id"] == block_id

    # Changing the day re-places it.
    client.patch(f"/commitments/{cid}", json={"day": "Friday"})
    blocks = _blocks(client, cid)
    assert [(b["day_of_week"], b["slot_index"]) for b in blocks] == [("Friday", 2)]
    assert blocks[0]["id"] != block_id
