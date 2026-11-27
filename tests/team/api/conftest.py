"""Fixtures for the SQE Module 2 API tests (pytest + requests).

The tests talk to a RUNNING, seeded Ralph (tests/team/seed/seed_sqe.py):
    BASE_URL=http://localhost:8000 .venv/bin/pytest -c tests/team/api/pytest.ini

Every test creates the licences/assets it needs through the API and deletes
them afterwards, so runs are repeatable and independent of each other.
"""

import os
import uuid

import pytest
import requests

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000").rstrip("/")
USERS = {
    "manager": ("sqe_manager", "Sqe-Manager-1"),
    "clerk": ("sqe_clerk", "Sqe-Clerk-1"),
}


def url(path):
    return f"{BASE_URL}{path}"


def token(role):
    user, pw = USERS[role]
    r = requests.post(url("/api-token-auth/"), data={"username": user, "password": pw})
    r.raise_for_status()
    return r.json()["token"]


class Api:
    """Small requests wrapper bound to one role's token."""

    def __init__(self, role=None):
        self.s = requests.Session()
        if role:
            self.s.headers["Authorization"] = f"Token {token(role)}"

    def get(self, path, **kw):
        return self.s.get(url(path), **kw)

    def post(self, path, json=None, **kw):
        return self.s.post(url(path), json=json, **kw)

    def patch(self, path, json=None, **kw):
        return self.s.patch(url(path), json=json, **kw)

    def delete(self, path, **kw):
        return self.s.delete(url(path), **kw)


def first_id(api, path):
    r = api.get(path)
    r.raise_for_status()
    return r.json()["results"][0]["id"]


def _id(value):
    return value["id"] if isinstance(value, dict) else value


def unique(prefix="SQE-T", length=None):
    """Unique text; with length=N exactly N characters long."""
    raw = f"{prefix}-{uuid.uuid4().hex}"
    if length is None:
        return raw
    if length <= len(raw):
        return raw[-length:] if length else ""
    return raw + "x" * (length - len(raw))


@pytest.fixture(scope="session")
def manager():
    return Api("manager")


@pytest.fixture(scope="session")
def clerk():
    return Api("clerk")


@pytest.fixture(scope="session")
def anon():
    return Api()


@pytest.fixture(scope="session")
def refs(manager):
    """Ids of seeded reference data, looked up by business key."""
    pk_lic = manager.get("/api/licences/?niw=SQE-LIC-001").json()["results"][0]
    uk_lic = manager.get("/api/licences/?niw=SQE-LIC-002").json()["results"][0]
    asset = manager.get("/api/back-office-assets/?barcode=SQE-BO-001").json()["results"][0]
    return {
        "region_pk": _id(pk_lic["region"]),
        "region_uk": _id(uk_lic["region"]),
        "licence_type": _id(pk_lic["licence_type"]),
        "software": _id(pk_lic["software"]),
        "model": _id(asset["model"]),
        "warehouse": _id(asset["warehouse"]),
        "holder": first_id(manager, "/api/assetholders/?name=SQE Holding"),
        "user_clerk": first_id(manager, "/api/users/?username=sqe_clerk"),
        "user_manager": first_id(manager, "/api/users/?username=sqe_manager"),
    }


class Factory:
    """Creates test data through the API and removes it at teardown."""

    def __init__(self, api, refs):
        self.api, self.refs, self.created = api, refs, []

    def track(self, path, obj_id):
        self.created.append(f"{path}{obj_id}/")

    def licence(self, seats=5, region="region_pk", **extra):
        body = {
            "number_bought": seats,
            "region": self.refs[region],
            "licence_type": self.refs["licence_type"],
            "software": self.refs["software"],
            "niw": unique(),
            **extra,
        }
        r = self.api.post("/api/licences/", body)
        assert r.status_code == 201, r.text
        self.track("/api/licences/", r.json()["id"])
        return r.json()

    def asset(self, region="region_pk", status="new"):
        barcode = unique("SQE-TA")[:30]
        body = {
            "barcode": barcode,
            "hostname": barcode.lower(),
            "region": self.refs[region],
            "model": self.refs["model"],
            "warehouse": self.refs["warehouse"],
            "property_of": self.refs["holder"],
            "status": status,
        }
        r = self.api.post("/api/back-office-assets/", body)
        assert r.status_code == 201, r.text
        self.track("/api/back-office-assets/", r.json()["id"])
        return r.json()

    def assign(self, licence_id, asset_id, quantity=1):
        r = self.api.post(
            "/api/base-objects-licences/",
            {"licence": licence_id, "base_object": asset_id, "quantity": quantity},
        )
        if r.status_code == 201:
            self.track("/api/base-objects-licences/", r.json()["id"])
        return r

    def transition(self, asset_id, name, data=None):
        return self.api.post(
            f"/api/back_office/backofficeasset/{asset_id}/transitions/{name}/", data or {}
        )

    def status(self, asset_id):
        return self.api.get(f"/api/back-office-assets/{asset_id}/").json()["status"]

    def seats_used(self, licence_id):
        """Read back the shared record: seats held by assets + users.

        GET /api/licences/{id}/ embeds its asset assignments (base_objects) and
        user assignments (users) with their quantities. (The ?licence= filter on
        /api/base-objects-licences/ is silently ignored - endpoint weakness W1.)
        """
        lic = self.api.get(f"/api/licences/{licence_id}/").json()
        return sum(a["quantity"] for a in lic["base_objects"]) + sum(
            u["quantity"] for u in lic["users"]
        )

    def cleanup(self):
        for path in reversed(self.created):
            self.api.delete(path)


@pytest.fixture
def make(manager, refs):
    f = Factory(manager, refs)
    yield f
    f.cleanup()
