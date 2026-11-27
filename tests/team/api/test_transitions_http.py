"""BR3 state transitions over HTTP (POST .../transitions/<name>/).

Lifecycle configured by the seed:
    release   : {new, free}       -> in use   (assign user + licences)
    return    : {in use}          -> free     (unassign user + licences)
    liquidate : {free, damaged}   -> liquidated

Every allowed transition is exercised once, and at least one disallowed
transition from every state. Status and seat usage are read back after each.
"""

import pytest

STATES = ["new", "in use", "free", "damaged", "liquidated"]
ALLOWED = {
    ("new", "release"): "in use",
    ("free", "release"): "in use",
    ("in use", "return"): "free",
    ("free", "liquidate"): "liquidated",
    ("damaged", "liquidate"): "liquidated",
}
TRANSITIONS = ["release", "return", "liquidate"]
DISALLOWED = [(s, t) for s in STATES for t in TRANSITIONS if (s, t) not in ALLOWED]


def release_data(make, licence_ids=()):
    return {"user": make.refs["user_clerk"], "licences": list(licence_ids)}


@pytest.mark.parametrize(("state", "name"), sorted(ALLOWED), ids=lambda v: str(v))
def test_allowed_transition(make, state, name):
    asset = make.asset(status=state)
    data = release_data(make) if name == "release" else {}
    r = make.transition(asset["id"], name, data)
    assert r.status_code == 201, r.text
    assert make.status(asset["id"]) == ALLOWED[(state, name)]


@pytest.mark.parametrize(("state", "name"), DISALLOWED, ids=lambda v: str(v))
def test_disallowed_transition_is_rejected_and_state_unchanged(make, state, name):
    asset = make.asset(status=state)
    data = release_data(make) if name == "release" else {}
    r = make.transition(asset["id"], name, data)
    assert r.status_code == 400
    assert "wrong source status" in r.text
    assert make.status(asset["id"]) == state


def test_release_then_return_moves_seats_on_the_shared_record(make):
    lic = make.licence(seats=3)
    asset = make.asset()
    assert (
        make.transition(asset["id"], "release", release_data(make, [lic["id"]])).status_code == 201
    )
    assert make.seats_used(lic["id"]) == 1
    assert make.transition(asset["id"], "return").status_code == 201
    assert make.status(asset["id"]) == "free"
    assert make.seats_used(lic["id"]) == 0


def test_repeated_release_does_not_assign_twice(make):
    lic = make.licence(seats=3)
    asset = make.asset()
    make.transition(asset["id"], "release", release_data(make, [lic["id"]]))
    again = make.transition(asset["id"], "release", release_data(make, [lic["id"]]))
    assert again.status_code == 400
    assert make.seats_used(lic["id"]) == 1


@pytest.mark.xfail(strict=True, reason="SQE-D03: release transition skips the region rule")
def test_release_with_other_region_licence_is_rejected(make):
    lic = make.licence(seats=3, region="region_uk")
    asset = make.asset(region="region_pk")
    r = make.transition(asset["id"], "release", release_data(make, [lic["id"]]))
    assert r.status_code == 400
    assert make.seats_used(lic["id"]) == 0


@pytest.mark.xfail(strict=True, reason="SQE-D03: release transition skips the seat limit")
def test_release_with_full_licence_is_rejected(make):
    lic = make.licence(seats=1)
    make.assign(lic["id"], make.asset()["id"], 1)
    asset = make.asset()
    r = make.transition(asset["id"], "release", release_data(make, [lic["id"]]))
    assert r.status_code == 400
    assert make.seats_used(lic["id"]) == 1
