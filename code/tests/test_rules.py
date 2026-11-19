"""Constraint rules: the solver honours them and the API keeps the grid in sync."""
import pytest

from app.models import Commitment, CommitmentType, RuleType, ScheduleGrid, SchedulingRule
from app.solver import place_flexible_tasks, place_hard_deadlines, place_recurring_quotas
from tests.test_api import client  # noqa: F401 - reuse the in-memory client fixture


def _cells(grid, title):
    return [(s.day, s.slot_index) for s in grid.slots if s.occupied_by == title]


def _occupy(grid, day, slot_index):
    next(s for s in grid.slots if s.day == day and s.slot_index == slot_index).occupied_by = "x"


def _quota(target, slot_index=None, rules=()):
    return Commitment(
        id="q", title="Gym", commitment_type=CommitmentType.RECURRING_QUOTA,
        target_frequency=target, slot_index=slot_index, rules=list(rules),
    )


def test_affinity_moves_quota_into_its_band():
    evening = SchedulingRule(rule_type=RuleType.TIME_OF_DAY_AFFINITY, target_slot=2, hard=True)
    grid = place_recurring_quotas(ScheduleGrid.create_empty_week(), [_quota(2, slot_index=0, rules=[evening])])
    # Preferred slot 0 is morning; the closest evening slot is 8.
    assert _cells(grid, "Gym") == [("Monday", 8), ("Tuesday", 8)]


def test_affinity_uses_another_slot_in_band_when_preferred_is_taken():
    evening = SchedulingRule(rule_type=RuleType.TIME_OF_DAY_AFFINITY, target_slot=2, hard=True)
    grid = ScheduleGrid.create_empty_week()
    _occupy(grid, "Monday", 9)
    grid = place_recurring_quotas(grid, [_quota(1, slot_index=9, rules=[evening])])
    assert _cells(grid, "Gym") == [("Monday", 8)]


def test_separation_spreads_sessions_with_rest_days():
    rest = SchedulingRule(rule_type=RuleType.SEPARATION, target_slot=1, hard=True)
    grid = place_recurring_quotas(ScheduleGrid.create_empty_week(), [_quota(4, slot_index=9, rules=[rest])])
    assert [day for day, _ in _cells(grid, "Gym")] == ["Monday", "Wednesday", "Friday", "Sunday"]


def test_unsatisfiable_hard_rule_fails():
    rest = SchedulingRule(rule_type=RuleType.SEPARATION, target_slot=2, hard=True)
    with pytest.raises(ValueError, match=r"scheduled 3/4 under hard rule\(s\)"):
        place_recurring_quotas(ScheduleGrid.create_empty_week(), [_quota(4, slot_index=9, rules=[rest])])


def test_soft_rule_is_relaxed_with_a_warning():
    rest = SchedulingRule(rule_type=RuleType.SEPARATION, target_slot=2, hard=False)
    grid = place_recurring_quotas(ScheduleGrid.create_empty_week(), [_quota(4, slot_index=9, rules=[rest])])
    # Mon, Thu, Sun honour 2 rest days; the 4th session is placed without the rule.
    assert len(_cells(grid, "Gym")) == 4
    assert grid.warnings == ["'Gym': 1 block(s) placed outside its soft rule(s) (2 rest day(s) between sessions)"]


def test_energy_tiering_takes_earliest_hours_across_the_week():
    focus = SchedulingRule(rule_type=RuleType.ENERGY_TIERING, target_slot=1, hard=True)
    task = Commitment(
        id="f", title="DSA", commitment_type=CommitmentType.FLEXIBLE_TASK, required_blocks=3, rules=[focus],
    )
    grid = place_flexible_tasks(ScheduleGrid.create_empty_week(), [task])
    assert _cells(grid, "DSA") == [("Monday", 0), ("Tuesday", 0), ("Wednesday", 0)]


def test_deadline_respects_affinity_while_scheduling_backwards():
    morning = SchedulingRule(rule_type=RuleType.TIME_OF_DAY_AFFINITY, target_slot=0, hard=True)
    task = Commitment(
        id="d", title="Report", commitment_type=CommitmentType.HARD_DEADLINE,
        deadline_day="Wednesday", deadline_slot=6, required_blocks=2, rules=[morning],
    )
    grid = place_hard_deadlines(ScheduleGrid.create_empty_week(), [task])
    assert sorted(_cells(grid, "Report")) == [("Wednesday", 2), ("Wednesday", 3)]


def test_flexible_task_that_does_not_fit_is_reported_not_raised():
    morning = SchedulingRule(rule_type=RuleType.TIME_OF_DAY_AFFINITY, target_slot=0, hard=True)
    task = Commitment(
        id="f", title="Reading", commitment_type=CommitmentType.FLEXIBLE_TASK, required_blocks=30, rules=[morning],
    )
    grid = place_flexible_tasks(ScheduleGrid.create_empty_week(), [task])
    assert len(_cells(grid, "Reading")) == 28  # 4 morning slots x 7 days
    assert grid.warnings[0].startswith("'Reading': only 28/30 block(s) fit under hard rule(s)")


# ---- API -------------------------------------------------------------------

def _blocks(client, commitment_id):
    return sorted(
        (b["day_of_week"], b["slot_index"])
        for b in client.get("/scheduled-blocks").json()
        if b["commitment_id"] == commitment_id
    )


def _gym(client, target=2, slot_index=0):
    return client.post(
        "/commitments",
        json={"title": "Gym", "type": "RECURRING_QUOTA", "target_per_week": target, "slot_index": slot_index},
    ).json()["id"]


def test_adding_a_rule_re_places_the_commitment(client):
    gym = _gym(client)
    assert _blocks(client, gym) == [("Monday", 0), ("Tuesday", 0)]

    res = client.post(
        "/constraint-rules",
        json={"commitment_id": gym, "rule_type": "TIME_OF_DAY_AFFINITY", "target_slot": 2, "strictness": "HARD"},
    )
    assert res.status_code == 201
    assert res.json()["warnings"] == []
    assert _blocks(client, gym) == [("Monday", 8), ("Tuesday", 8)]

    client.delete(f"/constraint-rules/{res.json()['id']}")
    assert _blocks(client, gym) == [("Monday", 0), ("Tuesday", 0)]


def test_soft_rule_warning_uses_the_title(client):
    gym = _gym(client, target=4, slot_index=9)
    res = client.post(
        "/constraint-rules",
        json={"commitment_id": gym, "rule_type": "SEPARATION", "target_slot": 2, "strictness": "SOFT"},
    )
    assert res.status_code == 201
    assert res.json()["warnings"] == [
        "'Gym': 1 block(s) placed outside its soft rule(s) (2 rest day(s) between sessions)"
    ]


def test_unsatisfiable_hard_rule_is_rejected_and_nothing_changes(client):
    gym = _gym(client, target=4, slot_index=9)
    before = _blocks(client, gym)
    res = client.post(
        "/constraint-rules",
        json={"commitment_id": gym, "rule_type": "SEPARATION", "target_slot": 2, "strictness": "HARD"},
    )
    assert res.status_code == 409
    assert res.json()["detail"].startswith("Could not fulfill quota for 'Gym'")
    assert client.get("/constraint-rules").json() == []
    assert _blocks(client, gym) == before


@pytest.mark.parametrize(
    ("commitment", "rule", "message"),
    [
        ({"title": "Lecture", "type": "FIXED_EVENT", "day": "Monday", "slot_index": 1},
         {"rule_type": "TIME_OF_DAY_AFFINITY", "target_slot": 0}, "Fixed events"),
        ({"title": "Reading", "type": "FLEXIBLE_TASK"},
         {"rule_type": "SEPARATION", "target_slot": 1}, "recurring quotas only"),
        ({"title": "Reading", "type": "FLEXIBLE_TASK"},
         {"rule_type": "TIME_OF_DAY_AFFINITY", "target_slot": 5}, "0 (morning)"),
    ],
)
def test_invalid_rules_are_rejected(client, commitment, rule, message):
    commitment_id = client.post("/commitments", json=commitment).json()["id"]
    res = client.post("/constraint-rules", json={"commitment_id": commitment_id, **rule})
    assert res.status_code == 422
    assert message in res.json()["detail"]


def test_placement_conflict_message_names_the_commitment(client):
    client.post("/commitments", json={"title": "Lecture", "type": "FIXED_EVENT", "day": "Monday", "slot_index": 0})
    client.post("/commitments", json={"title": "Lab", "type": "FIXED_EVENT", "day": "Tuesday", "slot_index": 0})
    res = client.post(
        "/commitments",
        json={"title": "Run", "type": "RECURRING_QUOTA", "target_per_week": 7, "slot_index": 0},
    )
    assert res.status_code == 409
    assert res.json()["detail"] == "Could not fulfill quota for 'Run': scheduled 5/7"


# ---- logged blocks survive re-placement and count towards their target -------

def _complete(client, commitment_id, day, slot_index):
    block = next(
        b for b in client.get("/scheduled-blocks").json()
        if b["commitment_id"] == commitment_id and (b["day_of_week"], b["slot_index"]) == (day, slot_index)
    )
    client.patch(f"/scheduled-blocks/{block['id']}", json={"status": "COMPLETED"})


def test_rule_change_keeps_logged_sessions_and_tops_up_to_target(client):
    gym = _gym(client)  # Monday 0, Tuesday 0
    _complete(client, gym, "Monday", 0)
    client.post(
        "/constraint-rules",
        json={"commitment_id": gym, "rule_type": "TIME_OF_DAY_AFFINITY", "target_slot": 2, "strictness": "HARD"},
    )
    # Monday's session already happened and stays; only one more is needed,
    # and not on Monday again.
    assert _blocks(client, gym) == [("Monday", 0), ("Tuesday", 8)]


def test_reslot_counts_logged_flexible_blocks(client):
    task = client.post(
        "/commitments", json={"title": "DSA", "type": "FLEXIBLE_TASK", "duration_blocks": 2}
    ).json()["id"]
    client.post("/scheduled-blocks", json={"commitment_id": task, "day_of_week": "Friday", "slot_index": 5})
    _complete(client, task, "Friday", 5)
    client.post("/schedule/reslot-flexible")
    assert _blocks(client, task) == [("Friday", 5), ("Monday", 0)]


def test_full_solve_does_not_stack_blocks_on_logged_ones(client):
    gym = _gym(client)
    _complete(client, gym, "Monday", 0)
    res = client.post("/schedule/solve")
    assert res.status_code == 200
    assert _blocks(client, gym) == [("Monday", 0), ("Tuesday", 0)]
    cells = [(b["day_of_week"], b["slot_index"]) for b in client.get("/scheduled-blocks").json()]
    assert len(cells) == len(set(cells))


# ---- statuses roll over weekly; history follows the block --------------------

def _next_week(monkeypatch):
    from datetime import timedelta

    from app import weeks

    real = weeks.now()
    monkeypatch.setattr(weeks, "now", lambda: real + timedelta(days=7))


def _grid_status(client, day, slot_index):
    return next(
        s["status"] for s in client.get("/schedule").json()["slots"]
        if (s["day_of_week"], s["slot_index"]) == (day, slot_index)
    )


def test_status_reads_as_planned_once_its_week_is_over(client, monkeypatch):
    gym = _gym(client)
    _complete(client, gym, "Monday", 0)
    assert _grid_status(client, "Monday", 0) == "COMPLETED"

    _next_week(monkeypatch)
    assert _grid_status(client, "Monday", 0) == "PLANNED"


def test_last_weeks_block_moves_with_its_history(client, monkeypatch):
    gym = _gym(client, target=1)
    block_id = next(b["id"] for b in client.get("/scheduled-blocks").json() if b["commitment_id"] == gym)
    client.post("/execution-logs", json={"block_id": block_id, "completed": True})
    _complete(client, gym, "Monday", 0)

    _next_week(monkeypatch)
    client.post(
        "/constraint-rules",
        json={"commitment_id": gym, "rule_type": "TIME_OF_DAY_AFFINITY", "target_slot": 2, "strictness": "HARD"},
    )
    # Last week's session no longer pins the block: it moves to the evening,
    # as the same row, so its log - and last week's streak - survive.
    blocks = [b for b in client.get("/scheduled-blocks").json() if b["commitment_id"] == gym]
    assert [(b["id"], b["day_of_week"], b["slot_index"]) for b in blocks] == [(block_id, "Monday", 8)]
    assert [log["block_id"] for log in client.get("/execution-logs").json()] == [block_id]
    [quota] = client.get("/insights/consistency").json()["quotas"]
    assert (quota["completed_this_week"], quota["streak"]) == (0, 1)
