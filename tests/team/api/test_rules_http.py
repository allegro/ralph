"""Business rules over HTTP, with read-back of the shared record (seat usage).

BR1 seat limit (BVA at free = 1), BR2 region decision table, BR4 repeated
requests, plus the other write paths that change seat usage.
"""

import pytest


# ---------------- BR1: seat limit, 3-point BVA around free seats ----------------


def test_br1_bva_around_last_free_seat_with_read_back(make):
    lic = make.licence(seats=5)
    assert make.assign(lic["id"], make.asset()["id"], 4).status_code == 201
    assert make.seats_used(lic["id"]) == 4  # free = 1

    r = make.assign(lic["id"], make.asset()["id"], 2)  # just above the limit
    assert r.status_code == 400 and "Not enough free seats" in r.text
    assert make.seats_used(lic["id"]) == 4  # rejection changed nothing

    r = make.assign(lic["id"], make.asset()["id"], 0)  # below the lower bound
    assert r.status_code == 400
    assert make.seats_used(lic["id"]) == 4

    assert make.assign(lic["id"], make.asset()["id"], 1).status_code == 201  # exactly at
    assert make.seats_used(lic["id"]) == 5

    r = make.assign(lic["id"], make.asset()["id"], 1)  # licence now full
    assert r.status_code == 400
    assert make.seats_used(lic["id"]) == 5


def test_br1_deleting_an_assignment_frees_its_seats(make):
    lic = make.licence(seats=2)
    r = make.assign(lic["id"], make.asset()["id"], 2)
    assert make.seats_used(lic["id"]) == 2
    assert make.api.delete(f"/api/base-objects-licences/{r.json()['id']}/").status_code == 204
    make.created.remove(f"/api/base-objects-licences/{r.json()['id']}/")
    assert make.seats_used(lic["id"]) == 0
    assert make.assign(lic["id"], make.asset()["id"], 2).status_code == 201


@pytest.mark.xfail(strict=True, reason="SQE-D05: seat limit not enforced for user assignments")
def test_br1_user_assignment_cannot_exceed_seats(make):
    lic = make.licence(seats=2)
    r = make.api.post(
        "/api/licence-users/",
        {"licence": lic["id"], "user": make.refs["user_clerk"], "quantity": 5},
    )
    if r.status_code == 201:
        make.track("/api/licence-users/", r.json()["id"])
    assert r.status_code == 400
    assert make.seats_used(lic["id"]) == 0


@pytest.mark.xfail(strict=True, reason="SQE-D06: number_bought can be reduced below seats in use")
def test_br1_licence_cannot_shrink_below_used_seats(make):
    lic = make.licence(seats=5)
    make.assign(lic["id"], make.asset()["id"], 4)
    r = make.api.patch(f"/api/licences/{lic['id']}/", {"number_bought": 2})
    assert r.status_code == 400


@pytest.mark.xfail(strict=True, reason="SQE-D07: PATCH quantity crashes with HTTP 500")
def test_br1_patch_quantity_above_free_is_rejected_cleanly(make):
    lic = make.licence(seats=5)
    r = make.assign(lic["id"], make.asset()["id"], 1)
    r = make.api.patch(f"/api/base-objects-licences/{r.json()['id']}/", {"quantity": 9})
    assert r.status_code == 400  # observed: 500 Server Error


# ---------------- BR2: region decision table over HTTP ----------------
# Conditions: A asset is back-office (always true for these endpoints' data),
# B licence given, C regions differ.  Rule: reject if A and B and C.
#   R1  B=F           -> 400 (licence is required by the API)
#   R2  B=T, C=F      -> 201 accept
#   R3  B=T, C=T      -> 400 region error, nothing written


def test_br2_r1_licence_missing_is_rejected(make):
    r = make.api.post(
        "/api/base-objects-licences/", {"base_object": make.asset()["id"], "quantity": 1}
    )
    assert r.status_code == 400 and "licence" in r.json()


def test_br2_r2_same_region_is_accepted(make):
    lic = make.licence(seats=3, region="region_pk")
    assert make.assign(lic["id"], make.asset(region="region_pk")["id"]).status_code == 201
    assert make.seats_used(lic["id"]) == 1


def test_br2_r3_different_region_is_rejected(make):
    lic = make.licence(seats=3, region="region_pk")
    r = make.assign(lic["id"], make.asset(region="region_uk")["id"])
    assert r.status_code == 400
    assert "different region" in r.text
    assert make.seats_used(lic["id"]) == 0


# ---------------- BR4: repeated requests create no duplicates ----------------


def test_br4_repeated_identical_request_creates_one_assignment(make):
    lic = make.licence(seats=5)
    asset = make.asset()
    first = make.assign(lic["id"], asset["id"], 1)
    second = make.assign(lic["id"], asset["id"], 1)
    assert first.status_code == 201
    assert second.status_code == 400  # "must make a unique set"
    assert make.seats_used(lic["id"]) == 1


def test_br4_duplicate_inventory_number_is_rejected(make):
    lic = make.licence(seats=1)
    r = make.api.post(
        "/api/licences/",
        {
            "number_bought": 1,
            "region": make.refs["region_pk"],
            "licence_type": make.refs["licence_type"],
            "software": make.refs["software"],
            "niw": lic["niw"],
        },
    )
    assert r.status_code == 400 and "niw" in r.json()


@pytest.mark.xfail(strict=True, reason="SQE-W1: ?licence= filter on assignments is ignored")
def test_assignment_list_filter_by_licence(make):
    lic = make.licence(seats=1)
    make.assign(lic["id"], make.asset()["id"])
    other = make.licence(seats=1)
    make.assign(other["id"], make.asset()["id"])
    rows = make.api.get(f"/api/base-objects-licences/?licence={lic['id']}").json()["results"]
    assert {row["licence"].rstrip("/").split("/")[-1] for row in rows} == {str(lic["id"])}
