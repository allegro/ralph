"""UC-2 Assign a licence to an asset (actor: Asset Manager) - every flow automated.

Main flow and A1/E1/E2 use the asset's "Licence" tab; A2 uses the licence's
"Assignments" tab. Each test checks the screen AND the postcondition (seats in
use, read back through the API). All data is created per test and removed.
"""

from conftest import BASE_URL, login, pick


def asset_licence_tab(page, asset_id):
    page.goto(f"{BASE_URL}/back_office/backofficeasset/{asset_id}/back_office_asset_licence/")


def licence_assignments_tab(page, licence_id):
    page.goto(f"{BASE_URL}/licences/licence/{licence_id}/assignments/")


def save(page):
    page.locator("input[type=submit][value=Save]").click()
    page.wait_for_load_state("networkidle")


def free_on_licence_page(page, licence_id):
    page.goto(f"{BASE_URL}/licences/licence/{licence_id}/change/")
    row = page.locator(".field-row", has=page.locator("label", has_text="Free"))
    return row.locator(".read-only").inner_text().strip()


def assign_from_asset(page, asset, lic, quantity=1, row=0):
    pick(page, f"id_licences-{row}-licence", lic["niw"])
    q = page.locator(f"#id_licences-{row}-quantity")
    q.fill(str(quantity))


# ------------------------------- UC-2 flows -------------------------------


def test_uc2_main_assign_one_seat_from_asset(page, data):
    lic = data.licence(seats=3)
    asset = data.asset()
    login(page, "manager")
    asset_licence_tab(page, asset["id"])
    assign_from_asset(page, asset, lic, quantity=1)
    save(page)
    assert "different region" not in page.content()
    assert "Not enough free seats" not in page.content()
    assert data.seats_used(lic["id"]) == 1
    assert free_on_licence_page(page, lic["id"]) == "2"


def test_uc2_a1_assign_two_seats(page, data):
    lic = data.licence(seats=3)
    asset = data.asset()
    login(page, "manager")
    asset_licence_tab(page, asset["id"])
    assign_from_asset(page, asset, lic, quantity=2)
    save(page)
    assert data.seats_used(lic["id"]) == 2
    assert free_on_licence_page(page, lic["id"]) == "1"


def test_uc2_a2_assign_from_the_licence_side(page, data):
    lic = data.licence(seats=2)
    asset = data.asset()
    login(page, "manager")
    licence_assignments_tab(page, lic["id"])
    pick(page, "id_baseobjectlicence_set-0-base_object", asset["barcode"])
    page.fill("#id_baseobjectlicence_set-0-quantity", "1")
    save(page)
    assert data.seats_used(lic["id"]) == 1
    assert free_on_licence_page(page, lic["id"]) == "1"


def test_uc2_e1_asset_in_other_region_is_refused(page, data):
    lic = data.licence(seats=3)  # PK licence
    asset = data.asset(region="region_uk")  # UK asset
    login(page, "manager")
    asset_licence_tab(page, asset["id"])
    assign_from_asset(page, asset, lic, quantity=1)
    save(page)
    assert "Asset region is in a different region than licence" in page.content()
    assert data.seats_used(lic["id"]) == 0


def test_uc2_e2_not_enough_seats_is_refused(page, data):
    lic = data.licence(seats=1)
    asset = data.asset()
    login(page, "manager")
    asset_licence_tab(page, asset["id"])
    assign_from_asset(page, asset, lic, quantity=2)  # asks for 2 of 1
    save(page)
    assert "Not enough free seats" in page.content()  # message added by the D01 fix
    assert data.seats_used(lic["id"]) == 0
