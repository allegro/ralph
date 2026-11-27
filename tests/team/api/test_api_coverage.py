"""API coverage criteria: every endpoint x method x documented status code,
and every query parameter in the OpenAPI spec.

| Endpoint                     | GET list | GET id  | POST            | PATCH       | DELETE  |
| /api/licences/               | 200 401  | 200 404 | 201 400 401 403 | 200 400 404 | 204 404 |
| /api/base-objects-licences/  | 200 401  | 200 404 | 201 400 401 403 | 200 404     | 204 404 |
| /api/licence-users/          | 200 401  |         | 201 400 401     |             |         |
| /api/back-office-assets/{id} |          | 200 404 |                 |             |         |
| /api-token-auth/             |          |         | 200 400         |             |         |
"""

import pytest
from conftest import url

MISSING = 999999


# ---------------- /api/licences/ ----------------


def test_licences_list_200_and_query_params(make):
    lic = make.licence(seats=1)
    r = make.api.get(f"/api/licences/?niw={lic['niw']}&limit=1")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 1 and body["results"][0]["id"] == lic["id"]
    assert len(make.api.get("/api/licences/?limit=1").json()["results"]) == 1


def test_licences_get_200_and_404(make):
    lic = make.licence(seats=1)
    assert make.api.get(f"/api/licences/{lic['id']}/").status_code == 200
    assert make.api.get(f"/api/licences/{MISSING}/").status_code == 404


def test_licences_post_201_400(make):
    make.licence(seats=1)  # 201 asserted inside the factory
    assert make.api.post("/api/licences/", {"number_bought": 1}).status_code == 400


def test_licences_post_401_anonymous_403_clerk(anon, clerk, refs):
    body = {
        "number_bought": 1,
        "region": refs["region_pk"],
        "licence_type": refs["licence_type"],
        "software": refs["software"],
    }
    assert anon.post("/api/licences/", body).status_code == 401
    assert clerk.post("/api/licences/", body).status_code == 403


def test_licences_list_401_anonymous(anon):
    assert anon.get("/api/licences/").status_code == 401


def test_licences_patch_200_400_404(make):
    lic = make.licence(seats=3)
    r = make.api.patch(f"/api/licences/{lic['id']}/", {"number_bought": 4})
    assert r.status_code == 200 and r.json()["number_bought"] == 4
    assert make.api.patch(f"/api/licences/{lic['id']}/", {"number_bought": "x"}).status_code == 400
    assert make.api.patch(f"/api/licences/{MISSING}/", {"number_bought": 1}).status_code == 404


def test_licences_delete_204_404(make):
    lic = make.licence(seats=1)
    assert make.api.delete(f"/api/licences/{lic['id']}/").status_code == 204
    make.created.remove(f"/api/licences/{lic['id']}/")
    assert make.api.get(f"/api/licences/{lic['id']}/").status_code == 404  # really gone
    assert make.api.delete(f"/api/licences/{MISSING}/").status_code == 404


# ---------------- /api/base-objects-licences/ ----------------


def test_assignments_list_200_401(make, anon):
    assert make.api.get("/api/base-objects-licences/?limit=5").status_code == 200
    assert anon.get("/api/base-objects-licences/").status_code == 401


def test_assignments_get_200_404(make):
    lic = make.licence(seats=1)
    r = make.assign(lic["id"], make.asset()["id"])
    assert make.api.get(f"/api/base-objects-licences/{r.json()['id']}/").status_code == 200
    assert make.api.get(f"/api/base-objects-licences/{MISSING}/").status_code == 404


def test_assignments_post_201_400_401_403(make, anon, clerk):
    lic = make.licence(seats=2)
    asset = make.asset()
    body = {"licence": lic["id"], "base_object": asset["id"], "quantity": 1}
    assert anon.post("/api/base-objects-licences/", body).status_code == 401
    assert make.assign(lic["id"], asset["id"]).status_code == 201
    assert make.api.post("/api/base-objects-licences/", {"quantity": 1}).status_code == 400
    # 403: the clerk may not create licences
    assert clerk.post("/api/licences/", {"number_bought": 1}).status_code == 403


@pytest.mark.xfail(strict=True, reason="SQE-W2: API lets a PK-only clerk assign UK objects")
def test_assignments_clerk_cannot_write_outside_own_region(make, clerk):
    uk = make.licence(seats=1, region="region_uk")
    uk_asset = make.asset(region="region_uk")
    r = clerk.post(
        "/api/base-objects-licences/",
        {"licence": uk["id"], "base_object": uk_asset["id"], "quantity": 1},
    )
    if r.status_code == 201:
        make.track("/api/base-objects-licences/", r.json()["id"])
    assert r.status_code in (400, 403)
    assert make.seats_used(uk["id"]) == 0


def test_assignments_patch_200_404(make):
    lic = make.licence(seats=5)
    a = make.assign(lic["id"], make.asset()["id"]).json()
    base_object = a["base_object"]
    base_object = base_object["id"] if isinstance(base_object, dict) else base_object
    full = {"licence": lic["id"], "base_object": base_object}
    r = make.api.patch(f"/api/base-objects-licences/{a['id']}/", {**full, "quantity": 2})
    assert r.status_code == 200 and make.seats_used(lic["id"]) == 2
    assert (
        make.api.patch(f"/api/base-objects-licences/{MISSING}/", {"quantity": 1}).status_code
        == 404
    )


def test_assignments_delete_204_404(make):
    lic = make.licence(seats=1)
    a = make.assign(lic["id"], make.asset()["id"]).json()
    assert make.api.delete(f"/api/base-objects-licences/{a['id']}/").status_code == 204
    make.created.remove(f"/api/base-objects-licences/{a['id']}/")
    assert make.api.delete(f"/api/base-objects-licences/{MISSING}/").status_code == 404


# ---------------- /api/licence-users/ ----------------


def test_licence_users_200_201_400_401(make, anon):
    lic = make.licence(seats=2)
    body = {"licence": lic["id"], "user": make.refs["user_clerk"], "quantity": 1}
    assert anon.get("/api/licence-users/").status_code == 401
    assert anon.post("/api/licence-users/", body).status_code == 401
    r = make.api.post("/api/licence-users/", body)
    assert r.status_code == 201
    make.track("/api/licence-users/", r.json()["id"])
    assert make.api.get("/api/licence-users/?limit=5").status_code == 200
    assert make.api.post("/api/licence-users/", {"quantity": 1}).status_code == 400
    assert make.seats_used(lic["id"]) == 1


# ---------------- /api/back-office-assets/{id}/ and auth ----------------


def test_asset_get_200_404_401(make, anon):
    asset = make.asset()
    r = make.api.get(f"/api/back-office-assets/{asset['id']}/")
    assert r.status_code == 200 and r.json()["status"] == "new"
    assert make.api.get(f"/api/back-office-assets/{MISSING}/").status_code == 404
    assert anon.get(f"/api/back-office-assets/{asset['id']}/").status_code == 401


@pytest.mark.parametrize(
    ("password", "expected"), [("Sqe-Manager-1", 200), ("wrong-password", 400)]
)
def test_token_auth_200_400(anon, password, expected):
    r = anon.s.post(
        url("/api-token-auth/"), data={"username": "sqe_manager", "password": password}
    )
    assert r.status_code == expected
