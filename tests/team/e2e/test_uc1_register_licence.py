"""UC-1 Register a licence (actor: Asset Manager) - every flow automated,
plus a keyboard-only check of the same form.

Each test checks what the screen shows AND the postcondition, read back
through the API. Every licence a test creates is deleted afterwards.
"""

import re
import uuid

from conftest import BASE_URL, login, pick

ADD_URL = f"{BASE_URL}/licences/licence/add/"


def new_niw():
    return f"SQE-UC1-{uuid.uuid4().hex[:8]}"


def find_licence(data, niw):
    """Return the licence with this inventory number (or None) and register it
    for clean-up."""
    res = data.get(f"/api/licences/?niw={niw}")["results"]
    if res:
        path = f"/api/licences/{res[0]['id']}/"
        if path not in data.created:
            data.created.append(path)
        return res[0]
    return None


def ref(v):
    return v["id"] if isinstance(v, dict) else v


def fill_form(page, niw, seats="5", region="PK-Islamabad", valid_thru=None):
    page.goto(ADD_URL)
    page.select_option("#id_licence_type", label="per user")
    pick(page, "id_software", "Office 365", "Office 365 E3")
    page.fill("#id_niw", niw)
    page.select_option("#id_region", label=region)
    if seats is not None:
        page.fill("#id_number_bought", seats)
    if valid_thru:
        page.click("#id_valid_thru")
        page.keyboard.press("Control+A")
        page.keyboard.type(valid_thru, delay=60)  # real key presses, like a user
        page.locator("#content-main h1").click()  # page title "Add licence" (not the logo link)
        page.wait_for_timeout(300)
        shown = page.input_value("#id_valid_thru")
        assert shown == valid_thru, f"date picker changed {valid_thru!r} to {shown!r}"


def save(page):
    page.locator("input[type=submit][value=Save]").click()
    page.wait_for_load_state("networkidle")


def read_only(page, label):
    row = page.locator(".field-row", has=page.locator("label", has_text=label))
    return row.locator(".read-only").inner_text().strip()


# ------------------------------- UC-1 flows -------------------------------


def test_uc1_main_register_licence(page, data):
    niw = new_niw()
    login(page, "manager")
    fill_form(page, niw, seats="5", valid_thru="2027-12-31")
    save(page)
    # screen: the new licence's page, 5 free / 0 used
    assert re.search(r"/licences/licence/\d+/change/", page.url), page.url
    assert read_only(page, "Free") == "5"
    assert read_only(page, "Used") == "0"
    # postcondition
    lic = find_licence(data, niw)
    assert lic is not None
    assert lic["number_bought"] == 5
    assert ref(lic["region"]) == data.refs["region_pk"]
    assert str(lic["valid_thru"]).startswith("2027-12-31")


def test_uc1_a1_perpetual_licence_without_valid_thru(page, data):
    niw = new_niw()
    login(page, "manager")
    fill_form(page, niw, seats="2")
    save(page)
    lic = find_licence(data, niw)
    assert lic is not None
    assert lic["valid_thru"] in (None, "")


def test_uc1_a2_register_for_another_region(page, data):
    niw = new_niw()
    login(page, "manager")
    fill_form(page, niw, seats="1", region="UK-London")
    save(page)
    lic = find_licence(data, niw)
    assert lic is not None
    assert ref(lic["region"]) == data.refs["region_uk"]


def test_uc1_e1_missing_number_bought_is_rejected(page, data):
    niw = new_niw()
    login(page, "manager")
    fill_form(page, niw, seats=None)
    save(page)
    assert "/licences/licence/add/" in page.url  # stayed on the form
    assert find_licence(data, niw) is None  # nothing saved


def test_uc1_e2_duplicate_inventory_number_is_rejected(page, data):
    login(page, "manager")
    fill_form(page, "SQE-LIC-001", seats="3")  # already used by the seed
    save(page)
    assert "/licences/licence/add/" in page.url
    assert data.get("/api/licences/?niw=SQE-LIC-001")["count"] == 1


# ---------------------------- keyboard-only ----------------------------

FOCUS_JS = """() => {
  const el = document.activeElement;
  const ac = el && el.closest ? el.closest('auto-complete') : null;
  return ac ? ac.id : (el && el.id) || '';
}"""


def test_uc1_keyboard_reaches_every_required_field_in_order(page):
    """Tab from the first field: focus must reach the required fields in the
    order they are shown, then the Save button."""
    login(page, "manager")
    page.goto(ADD_URL)
    page.focus("#id_licence_type")
    wanted = ["id_licence_type", "id_software", "id_niw", "id_region", "id_number_bought"]
    seen = [page.evaluate(FOCUS_JS)]
    for _ in range(80):
        page.keyboard.press("Tab")
        f = page.evaluate(FOCUS_JS)
        if f != seen[-1]:
            seen.append(f)
        if page.evaluate("() => document.activeElement.value === 'Save'"):
            seen.append("SAVE")
            break
    order = [f for f in seen if f in wanted]
    assert order == wanted, f"focus order was {seen}"
    assert seen[-1] == "SAVE", f"Save button never reached by Tab: {seen}"


def test_uc1_keyboard_only_registration(page, data):
    """Complete UC-1 without the mouse. page.focus() is used only to skip the
    optional fields between the required ones (same as a user pressing Tab
    several times); every value is entered with the keyboard."""
    niw = new_niw()
    login(page, "manager")
    page.goto(ADD_URL)
    page.focus("#id_licence_type")
    page.keyboard.press("ArrowDown")  # -> "per user"
    # move to the Software search box with Tab
    for _ in range(20):
        page.keyboard.press("Tab")
        if page.evaluate(FOCUS_JS) == "id_software":
            break
    page.keyboard.type("Office 365", delay=80)
    page.locator("auto-complete#id_software #suggestList paper-item").first.wait_for(
        state="visible", timeout=20000
    )
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Enter")
    page.wait_for_function(
        "() => document.querySelector('auto-complete#id_software input#values-input').value"
    )
    page.focus("#id_niw")
    page.keyboard.press("Control+A")
    page.keyboard.type(niw)
    page.focus("#id_region")
    page.keyboard.press("ArrowDown")  # region -> PK-Islamabad
    page.focus("#id_number_bought")
    page.keyboard.type("4")
    # every value must be in place before submitting - this names the field
    # the keyboard could not set, if any
    got = page.evaluate("""() => ({
      licence_type: document.querySelector('#id_licence_type').value,
      software: document.querySelector('auto-complete#id_software input#values-input').value,
      niw: document.querySelector('#id_niw').value,
      region: document.querySelector('#id_region').value,
      number_bought: document.querySelector('#id_number_bought').value,
    })""")
    missing = [k for k, v in got.items() if not v]
    assert not missing, f"keyboard could not set: {missing} (form values: {got})"
    assert got["niw"] == niw and got["number_bought"] == "4", got
    page.keyboard.press("Enter")  # submit the form
    try:
        page.wait_for_url(re.compile(r"/licences/licence/\d+/change/"), timeout=15000)
    except Exception:
        pass  # stayed on the form - reported below
    page.wait_for_load_state("networkidle")
    lic = find_licence(data, niw)
    if lic is None:
        errors = page.locator(".errorlist, .error, .alert-box").all_inner_texts()
        raise AssertionError(f"not saved; still on {page.url}; errors shown: {errors}")
    assert lic["number_bought"] == 4
