"""Automated usability task tests (brief section 3), one per workflow.

T1 (W1): test_uc1_register_licence.py::test_uc1_main_register_licence.
T2 (W2): below - submit a value the rule rejects, check the error says what to
correct, correct it, check success. Keyboard test: test_uc1_keyboard_*.
"""

from conftest import BASE_URL, login, pick


def test_t2_assign_rejected_value_then_correct_it(page, data):
    lic = data.licence(seats=1)
    asset = data.asset()
    login(page, "manager")
    page.goto(f"{BASE_URL}/back_office/backofficeasset/{asset['id']}/back_office_asset_licence/")

    pick(page, "id_licences-0-licence", lic["niw"])
    page.fill("#id_licences-0-quantity", "2")
    page.locator("input[type=submit][value=Save]").click()
    page.wait_for_load_state("networkidle")

    error = page.locator(".errorlist").first
    error.wait_for(state="visible")
    text = error.inner_text()
    assert "Not enough free seats" in text, text
    assert "requested 2" in text and "available 1" in text, text
    assert data.seats_used(lic["id"]) == 0

    hidden = page.locator("auto-complete#id_licences-0-licence input#values-input")
    if not hidden.input_value():
        pick(page, "id_licences-0-licence", lic["niw"])
    page.fill("#id_licences-0-quantity", "1")
    page.locator("input[type=submit][value=Save]").click()
    page.wait_for_load_state("networkidle")

    assert page.locator(".errorlist").count() == 0
    assert data.seats_used(lic["id"]) == 1
    page.goto(f"{BASE_URL}/licences/licence/{lic['id']}/change/")
    free = page.locator(".field-row", has=page.locator("label", has_text="Free"))
    assert free.locator(".read-only").inner_text().strip() == "0"
