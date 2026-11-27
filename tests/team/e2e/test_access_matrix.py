"""Area 3b - access matrix, verified in the browser (Playwright, Chromium).

Roles (seed_sqe.py): R1 SQE Asset Manager (all regions), R2 SQE Regional Clerk
(PK region only; view licences, add assignments; no licence create, no transitions).

| #  | Role      | Action                              | Expected |
| S1 | Manager   | Open "Add licence" form             | Allowed  |
| S2 | Clerk     | Open "Add licence" form             | Denied   |
| S3 | Clerk     | See licences in the list            | PK only  |
| S4 | Clerk     | Open UK licence SQE-LIC-002 by URL  | Denied   |
| S5 | Manager   | Open "release" transition form      | Allowed  |
| S6 | Clerk     | Open "release" transition form      | Denied   |
| S7 | Anonymous | GET /api/licences/                  | 401      |
| S8 | Clerk     | POST /api/licences/                 | 403      |
"""

import requests
from conftest import BASE_URL, api_token, login


def test_s1_manager_can_open_add_licence(page):
    login(page, "manager")
    resp = page.goto(f"{BASE_URL}/licences/licence/add/")
    assert resp.status == 200
    assert page.locator("#id_number_bought").count() == 1  # the seat field is there


def test_s2_clerk_cannot_open_add_licence(page):
    login(page, "clerk")
    resp = page.goto(f"{BASE_URL}/licences/licence/add/")
    assert resp.status == 403
    assert page.locator("#id_number_bought").count() == 0


def test_s3_clerk_sees_only_own_region_licences(page):
    login(page, "clerk")
    page.goto(f"{BASE_URL}/licences/licence/")
    body = page.content()
    assert "SQE-LIC-001" in body and "SQE-LIC-003" in body  # PK region
    assert "SQE-LIC-002" not in body  # UK region hidden


def test_s4_clerk_cannot_open_other_region_licence(page, ids):
    login(page, "clerk")
    page.goto(f"{BASE_URL}/licences/licence/{ids['lic_uk']}/change/")
    assert "/licences/licence/" not in page.url  # redirected away
    assert "SQE-LIC-002" not in page.content()


def test_s5_manager_can_open_release_transition(page, ids):
    login(page, "manager")
    url = f"{BASE_URL}/back_office/backofficeasset/{ids['asset_new']}/transition/{ids['release']}"
    resp = page.goto(url)
    assert resp.status == 200
    assert page.locator("form").count() >= 1


def test_s6_clerk_cannot_open_release_transition(page, ids):
    login(page, "clerk")
    url = f"{BASE_URL}/back_office/backofficeasset/{ids['asset_new']}/transition/{ids['release']}"
    resp = page.request.get(url)  # same logged-in session; Chrome won't render an empty 403
    assert resp.status == 403
    assert "<form" not in resp.text()


def test_s7_anonymous_api_is_rejected(page):
    resp = page.request.get(f"{BASE_URL}/api/licences/")
    assert resp.status == 401


def test_s8_clerk_cannot_create_licence_via_api(page):
    resp = page.request.post(
        f"{BASE_URL}/api/licences/",
        headers={"Authorization": f"Token {api_token('clerk')}"},
        data={"niw": "SQE-X-DENIED", "number_bought": 1},
    )
    assert resp.status == 403
    # nothing was created
    check = requests.get(
        f"{BASE_URL}/api/licences/?niw=SQE-X-DENIED",
        headers={"Authorization": f"Token {api_token('manager')}"},
    )
    assert check.json()["count"] == 0
