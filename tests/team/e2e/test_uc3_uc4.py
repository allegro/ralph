"""UC-3 Release an asset to a user / UC-4 Return an asset - every flow automated.

Each test asserts what the screen shows AND the postcondition, read back
through the API (status, user, licence seats in use).
"""

import re

import pytest
from conftest import BASE_URL, login, pick


def open_transition(page, asset_id, name):
    """Open the asset, use the Transitions dropdown like a user, pick `name`."""
    page.goto(f"{BASE_URL}/back_office/backofficeasset/{asset_id}/change/")
    page.locator("a.button.dropdown", has_text="Transitions").click()
    page.locator("#transitions_status a", has_text=name).click()
    page.wait_for_url(re.compile(r"/transition/\d+"))
    assert page.locator("h1", has_text=name).count() >= 1


def run(page):
    page.locator("button", has_text="Run transition").click()
    page.wait_for_load_state("networkidle")



def run_without_form(page, asset_id, name):
    """A transition with no form fields (here: return) runs as soon as its menu
    entry is clicked - Ralph executes it and redirects back to the asset."""
    page.goto(f"{BASE_URL}/back_office/backofficeasset/{asset_id}/change/")
    page.locator("a.button.dropdown", has_text="Transitions").click()
    page.locator("#transitions_status a", has_text=name).click()
    page.wait_for_url(re.compile(rf"/backofficeasset/{asset_id}/change/"))
    page.wait_for_load_state("networkidle")

def transition_names_offered(page, asset_id):
    page.goto(f"{BASE_URL}/back_office/backofficeasset/{asset_id}/change/")
    links = page.locator("#transitions_status a")
    return [t.strip() for t in links.all_inner_texts()]


# ------------------------------ UC-3 release ------------------------------


def test_uc3_main_release_new_asset_with_user_and_licence(page, data):
    lic = data.licence(seats=3)
    asset = data.asset(status="new")
    login(page, "manager")
    open_transition(page, asset["id"], "release")
    pick(page, "id_assign_licence__licences", lic["niw"])
    pick(page, "id_assign_user__user", "sqe_clerk")
    run(page)
    # screen: back on the asset, no form errors
    assert "/change/" in page.url
    assert page.locator(".errorlist").count() == 0
    # postconditions
    assert data.status(asset["id"]) == "in use"
    assert data.asset_user(asset["id"]) == data.refs["clerk"]
    assert data.seats_used(lic["id"]) == 1


def test_uc3_a1_release_from_free_state(page, data):
    asset = data.asset(status="free")
    login(page, "manager")
    open_transition(page, asset["id"], "release")
    pick(page, "id_assign_user__user", "sqe_clerk")
    run(page)
    assert data.status(asset["id"]) == "in use"


def test_uc3_a2_release_without_licence(page, data):
    lic = data.licence(seats=2)
    asset = data.asset(status="new")
    login(page, "manager")
    open_transition(page, asset["id"], "release")
    pick(page, "id_assign_user__user", "sqe_clerk")
    run(page)
    assert data.status(asset["id"]) == "in use"
    assert data.seats_used(lic["id"]) == 0  # no seat taken


@pytest.mark.parametrize("state", ["liquidated", "in use"])
def test_uc3_e1_release_not_offered_in_disallowed_state(page, data, state):
    asset = data.asset(status=state)
    login(page, "manager")
    assert "release" not in transition_names_offered(page, asset["id"])
    assert data.status(asset["id"]) == state


def test_uc3_e1b_user_is_required(page, data):
    asset = data.asset(status="new")
    login(page, "manager")
    open_transition(page, asset["id"], "release")
    run(page)  # submit without choosing a user
    assert "/transition/" in page.url  # stayed on the form
    assert data.status(asset["id"]) == "new"


@pytest.mark.xfail(strict=True, reason="SQE-D03: release assigns a fully used licence")
def test_uc3_e2_full_licence_is_refused(page, data):
    lic = data.licence(seats=1, name="SQE-UI-FULL")
    data.post(
        "/api/base-objects-licences/",
        {"licence": lic["id"], "base_object": data.asset()["id"], "quantity": 1},
    )
    asset = data.asset(status="new")
    login(page, "manager")
    open_transition(page, asset["id"], "release")
    pick(page, "id_assign_licence__licences", lic["niw"])
    pick(page, "id_assign_user__user", "sqe_clerk")
    run(page)
    assert data.seats_used(lic["id"]) == 1  # Ralph makes it 2 (over the limit)


# ------------------------------ UC-4 return ------------------------------


def released_asset(data, licences=()):
    asset = data.asset(status="new")
    data.transition(
        asset["id"],
        "release",
        {"user": data.refs["clerk"], "licences": [lic["id"] for lic in licences]},
    )
    assert data.status(asset["id"]) == "in use"
    return asset


def test_uc4_main_return_frees_asset_and_seat(page, data):
    lic = data.licence(seats=3)
    asset = released_asset(data, [lic])
    assert data.seats_used(lic["id"]) == 1
    login(page, "manager")
    run_without_form(page, asset["id"], "return")
    assert "/change/" in page.url
    assert data.status(asset["id"]) == "free"
    assert data.asset_user(asset["id"]) in (None, "")
    assert data.seats_used(lic["id"]) == 0


def test_uc4_a1_return_with_two_licences_releases_both(page, data):
    lic1, lic2 = data.licence(seats=2), data.licence(seats=2)
    asset = released_asset(data, [lic1, lic2])
    login(page, "manager")
    run_without_form(page, asset["id"], "return")
    assert data.seats_used(lic1["id"]) == 0 and data.seats_used(lic2["id"]) == 0


def test_uc4_a2_return_then_release_to_another_user(page, data):
    asset = released_asset(data)
    login(page, "manager")
    run_without_form(page, asset["id"], "return")
    open_transition(page, asset["id"], "release")
    pick(page, "id_assign_user__user", "sqe_manager")
    run(page)
    assert data.status(asset["id"]) == "in use"
    assert data.asset_user(asset["id"]) == data.refs["manager"]


def test_uc4_e1_clerk_cannot_run_return(page, data):
    asset = released_asset(data)
    login(page, "clerk")
    resp = page.request.get(f"{BASE_URL}/back_office/backofficeasset/{asset['id']}/change/")
    # the clerk cannot reach the transition at all
    return_url = None
    m = re.search(r'/transition/(\d+)">\s*return', resp.text())
    if m:
        return_url = (
            f"{BASE_URL}/back_office/backofficeasset/{asset['id']}/transition/{m.group(1)}"
        )
        assert page.request.get(return_url).status == 403
    assert data.status(asset["id"]) == "in use"


def test_uc4_e2_return_not_offered_when_already_free(page, data):
    asset = data.asset(status="free")
    login(page, "manager")
    assert "return" not in transition_names_offered(page, asset["id"])
    assert data.status(asset["id"]) == "free"
