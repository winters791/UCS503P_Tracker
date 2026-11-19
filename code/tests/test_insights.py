"""Consistency streaks and the weekly retrospective."""
from datetime import date, datetime, timedelta, timezone

from app.insights import Block, Item, Log, consistency, retrospective
from app.models import CommitmentType as T
from tests.test_api import client  # noqa: F401 - reuse the in-memory client fixture

IST = timezone(timedelta(hours=5, minutes=30))
WEDNESDAY = date(2026, 10, 28)  # this week starts Monday 2026-10-26

GYM = Item("gym", "Gym", T.RECURRING_QUOTA, target_per_week=2)
LECTURE = Item("lec", "SE Lecture", T.FIXED_EVENT)
GYM_MON = Block("g1", "gym", day_index=0, slot_index=9)
GYM_WED = Block("g2", "gym", day_index=2, slot_index=9)
LEC_MON = Block("l1", "lec", day_index=0, slot_index=1)
LEC_TUE = Block("l2", "lec", day_index=1, slot_index=0)
BLOCKS = [GYM_MON, GYM_WED, LEC_MON, LEC_TUE]


def at(d: date, hour: int = 20) -> datetime:
    return datetime(d.year, d.month, d.day, hour, tzinfo=IST)


def gym_week(monday: date, sessions: int) -> list[Log]:
    blocks = [GYM_MON, GYM_WED][:sessions]
    return [Log(b.id, True, at(monday + timedelta(days=b.day_index))) for b in blocks]


def test_streak_counts_closed_weeks_and_ignores_an_unfinished_current_week():
    logs = (
        gym_week(date(2026, 10, 5), 1)      # short - ends any streak before it
        + gym_week(date(2026, 10, 12), 2)
        + gym_week(date(2026, 10, 19), 2)
        + gym_week(date(2026, 10, 26), 1)   # this week, still in progress
    )
    [gym] = consistency([GYM, LECTURE], BLOCKS, logs, WEDNESDAY, weeks=4)
    assert (gym.completed_this_week, gym.target, gym.streak) == (1, 2, 2)
    assert [(w.week_start.day, w.completed, w.met) for w in gym.history] == [
        (5, 1, False), (12, 2, True), (19, 2, True), (26, 1, False),
    ]

    logs.append(Log(GYM_WED.id, True, at(WEDNESDAY)))
    [gym] = consistency([GYM], BLOCKS, logs, WEDNESDAY)
    assert gym.streak == 3


def test_a_closed_week_below_target_resets_the_streak():
    logs = gym_week(date(2026, 10, 12), 2) + gym_week(date(2026, 10, 19), 1)
    [gym] = consistency([GYM], BLOCKS, logs, WEDNESDAY)
    assert gym.streak == 0


def test_latest_log_in_a_week_wins():
    logs = [
        Log(GYM_MON.id, False, at(date(2026, 10, 26), 18)),
        Log(GYM_MON.id, True, at(date(2026, 10, 26), 21)),   # corrected to done
        Log(GYM_WED.id, True, at(WEDNESDAY, 18)),
        Log(GYM_WED.id, True, at(WEDNESDAY, 19)),            # logged twice
    ]
    [gym] = consistency([GYM], BLOCKS, logs, WEDNESDAY)
    assert gym.completed_this_week == 2


def test_retrospective_splits_past_and_upcoming_blocks():
    logs = [
        Log(LEC_MON.id, True, at(date(2026, 10, 26), 10)),
        Log(GYM_MON.id, False, at(date(2026, 10, 26), 19)),
        Log(GYM_MON.id, True, at(date(2026, 10, 19), 19)),  # last week - must not count
    ]
    now = at(WEDNESDAY, 12)  # Wednesday's 17:00 gym has not happened yet
    retro = retrospective([GYM, LECTURE], BLOCKS, logs, WEDNESDAY, now)

    t = retro.totals
    assert (t.planned, t.completed, t.missed, t.not_logged, t.upcoming, t.due) == (4, 1, 1, 1, 1, 3)
    assert (retro.week_start, retro.week_end) == (date(2026, 10, 26), date(2026, 11, 1))
    assert [(c.title, c.tally.completed, c.tally.missed) for c in retro.by_commitment] == [
        ("SE Lecture", 1, 0), ("Gym", 0, 1),
    ]
    assert [d.due for d in retro.by_day] == [2, 1, 0, 0, 0, 0, 0]
    assert [(q.title, q.completed, q.target, q.met) for q in retro.quota_results] == [("Gym", 0, 2, False)]
    assert retro.highlights == [
        "Completed 1 of 3 blocks that were due (33%).",
        "SE Lecture slipped the most: 1 of 2 not done.",
        "Tuesday was the weakest day (0/1 done).",
        "Hit 0 of 1 weekly targets - short on Gym 0/2.",
        "1 past block(s) were never logged.",
    ]


def test_retrospective_with_nothing_due_says_so():
    now = at(date(2026, 10, 26), 7)  # Monday before the first block
    retro = retrospective([GYM, LECTURE], BLOCKS, [], date(2026, 10, 26), now)
    assert retro.totals.upcoming == 4
    assert retro.highlights == ["Nothing to review yet - no blocks have come due this week."]


def test_insight_endpoints(client):
    gym = client.post(
        "/commitments", json={"title": "Gym", "type": "RECURRING_QUOTA", "target_per_week": 1, "slot_index": 0}
    ).json()["id"]
    block = next(b for b in client.get("/scheduled-blocks").json() if b["commitment_id"] == gym)
    client.post("/execution-logs", json={"block_id": block["id"], "completed": True})

    report = client.get("/insights/consistency").json()
    [quota] = report["quotas"]
    assert (quota["title"], quota["completed_this_week"], quota["target"], quota["streak"]) == ("Gym", 1, 1, 1)
    assert len(quota["history"]) == 8

    retro = client.get("/insights/retrospective").json()
    assert retro["totals"]["completed"] == 1
    assert retro["by_commitment"][0]["title"] == "Gym"

    last_week = client.get("/insights/retrospective", params={"week_start": "2020-01-08"}).json()
    assert last_week["week_start"] == "2020-01-06"  # snapped to Monday
    assert last_week["totals"]["completed"] == 0
