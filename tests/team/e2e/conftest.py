"""Playwright (Chromium) fixtures for the SQE end-to-end tests.

Run against a seeded Ralph server (default http://127.0.0.1:8000):
    BASE_URL=http://127.0.0.1:8000 ../../../.venv/bin/pytest -c pytest.ini
Optional OWASP ZAP passive proxy:  ZAP_PROXY=http://127.0.0.1:8090
"""

import os
import re
import uuid

import pytest
import requests

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
USERS = {
    "manager": ("sqe_manager", "Sqe-Manager-1"),
    "clerk": ("sqe_clerk", "Sqe-Clerk-1"),
}


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    args = dict(browser_type_launch_args)
    if os.environ.get("ZAP_PROXY"):
        args["proxy"] = {"server": os.environ["ZAP_PROXY"], "bypass": "<-loopback>"}
    return args


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    args = dict(browser_context_args)
    args.setdefault("viewport", {"width": 1366, "height": 900})
    if os.environ.get("ZAP_PROXY"):
        args["ignore_https_errors"] = True
    return args


@pytest.fixture(autouse=True)
def _hide_debug_toolbar(context):
    """Ralph's dev settings show the Django debug toolbar over the page."""
    host = BASE_URL.split("//", 1)[1].split(":")[0].split("/")[0]
    context.add_cookies([{"name": "djdt", "value": "hide", "domain": host, "path": "/"}])


def api_token(role):
    user, pw = USERS[role]
    r = requests.post(f"{BASE_URL}/api-token-auth/", data={"username": user, "password": pw})
    r.raise_for_status()
    return r.json()["token"]


@pytest.fixture(scope="session")
def ids():
    """Look up seeded objects by business key, never by hard-coded id."""
    h = {"Authorization": f"Token {api_token('manager')}"}

    def one(path):
        r = requests.get(f"{BASE_URL}{path}", headers=h)
        r.raise_for_status()
        return r.json()["results"][0]["id"]

    out = {
        "lic_pk": one("/api/licences/?niw=SQE-LIC-001"),
        "lic_uk": one("/api/licences/?niw=SQE-LIC-002"),
        "asset_new": one("/api/back-office-assets/?barcode=SQE-BO-001"),
    }
    # transition id: read from the manager's "current transitions" page
    s = requests.Session()
    page = s.get(f"{BASE_URL}/login/")
    tok = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', page.text).group(1)
    user, pw = USERS["manager"]
    s.post(
        f"{BASE_URL}/login/",
        data={"username": user, "password": pw, "csrfmiddlewaretoken": tok},
        headers={"Referer": f"{BASE_URL}/login/"},
    )
    html = s.get(f"{BASE_URL}/back_office/backofficeasset/{out['asset_new']}/change/").text
    links = dict(re.findall(r'/transition/(\d+)">\s*([\w-]+)', html)[::-1])
    named = {name.lower(): int(t) for t, name in links.items()}
    out["release"] = named["release"]
    return out


def login(page, role):
    user, pw = USERS[role]
    page.goto(f"{BASE_URL}/login/")
    page.fill("#id_username", user)
    page.fill("#id_password", pw)
    page.click("button.login")
    page.wait_for_url(re.compile(r"^(?!.*/login/).*"))


def pick(page, field_id, query, choice_text=None, timeout=20000):
    """Select a value in one of Ralph's <auto-complete> widgets like a user would:
    type into its search box, wait for the suggestion, click it. Returns the
    id written into the widget's hidden input (the value the form submits)."""
    widget = page.locator(f"auto-complete#{field_id}")
    box = widget.locator("input#text-getter")
    box.click()
    box.fill("")
    box.type(query, delay=80)
    item = widget.locator("#suggestList paper-item", has_text=choice_text or query).first
    item.wait_for(state="visible", timeout=timeout)
    item.click()
    hidden = widget.locator("input#values-input")
    page.wait_for_function(
        "el => el.value && el.value !== ''", arg=hidden.element_handle(), timeout=timeout
    )
    return hidden.input_value()


class ApiData:
    """Creates the data a UI test needs through the API and removes it afterwards."""

    def __init__(self):
        self.h = {"Authorization": f"Token {api_token('manager')}"}
        self.created = []

        def one(path):
            r = requests.get(f"{BASE_URL}{path}", headers=self.h)
            r.raise_for_status()
            return r.json()["results"][0]

        def _id(v):
            return v["id"] if isinstance(v, dict) else v

        lic = one("/api/licences/?niw=SQE-LIC-001")
        asset = one("/api/back-office-assets/?barcode=SQE-BO-001")
        self.refs = {
            "region_pk": _id(lic["region"]),
            "region_uk": _id(one("/api/licences/?niw=SQE-LIC-002")["region"]),
            "licence_type": _id(lic["licence_type"]),
            "software": _id(lic["software"]),
            "model": _id(asset["model"]),
            "warehouse": _id(asset["warehouse"]),
            "holder": one("/api/assetholders/?name=SQE Holding")["id"],
            "clerk": one("/api/users/?username=sqe_clerk")["id"],
            "manager": one("/api/users/?username=sqe_manager")["id"],
        }

    def post(self, path, body):
        r = requests.post(f"{BASE_URL}{path}", headers=self.h, json=body)
        assert r.status_code in (200, 201), f"{path}: {r.status_code} {r.text[:300]}"
        return r.json()

    def get(self, path):
        return requests.get(f"{BASE_URL}{path}", headers=self.h).json()

    def licence(self, seats=5, region="region_pk", name="SQE-UI"):
        niw = f"{name}-{uuid.uuid4().hex[:8]}"
        lic = self.post(
            "/api/licences/",
            {
                "number_bought": seats,
                "region": self.refs[region],
                "licence_type": self.refs["licence_type"],
                "software": self.refs["software"],
                "niw": niw,
            },
        )
        self.created.append(f"/api/licences/{lic['id']}/")
        return lic

    def asset(self, status="new", region="region_pk"):
        bc = f"SQE-UI-{uuid.uuid4().hex[:8]}"
        a = self.post(
            "/api/back-office-assets/",
            {
                "barcode": bc,
                "hostname": bc.lower(),
                "region": self.refs[region],
                "model": self.refs["model"],
                "warehouse": self.refs["warehouse"],
                "property_of": self.refs["holder"],
                "status": status,
            },
        )
        self.created.append(f"/api/back-office-assets/{a['id']}/")
        return a

    def transition(self, asset_id, name, data=None):
        return self.post(
            f"/api/back_office/backofficeasset/{asset_id}/transitions/{name}/", data or {}
        )

    def status(self, asset_id):
        return self.get(f"/api/back-office-assets/{asset_id}/")["status"]

    def asset_user(self, asset_id):
        u = self.get(f"/api/back-office-assets/{asset_id}/").get("user")
        return u["id"] if isinstance(u, dict) else u

    def seats_used(self, licence_id):
        lic = self.get(f"/api/licences/{licence_id}/")
        return sum(a["quantity"] for a in lic["base_objects"]) + sum(
            u["quantity"] for u in lic["users"]
        )

    def cleanup(self):
        for path in reversed(self.created):
            requests.delete(f"{BASE_URL}{path}", headers=self.h)


@pytest.fixture
def data():
    d = ApiData()
    yield d
    d.cleanup()


@pytest.fixture(autouse=True)
def _hide_overlays(context):
    """Hide the Django debug toolbar so it cannot cover buttons or suggestions."""
    context.add_init_script(
        """
        document.addEventListener('DOMContentLoaded', () => {
          const s = document.createElement('style');
          s.textContent = '#djDebug, #djDebugToolbar, #djDebugToolbarHandle '
                        + '{display:none !important; pointer-events:none !important;}';
          document.head.appendChild(s);
        });
        """
    )


@pytest.fixture(autouse=True)
def _hide_overlays(context):
    """Hide the Django debug toolbar so it cannot cover buttons or suggestions."""
    context.add_init_script(
        """
        document.addEventListener('DOMContentLoaded', () => {
          const s = document.createElement('style');
          s.textContent = '#djDebug, #djDebugToolbar, #djDebugToolbarHandle '
                        + '{display:none !important; pointer-events:none !important;}';
          document.head.appendChild(s);
        });
        """
    )
