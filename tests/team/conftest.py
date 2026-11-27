"""Shared fixtures for the SQE team test suite (tests/team).

All data is synthetic and created per test inside a rolled-back transaction,
so each test starts from a clean database (this is our "reset" between runs).
"""

import pytest


@pytest.fixture
def region_pk(db):
    from ralph.accounts.tests.factories import RegionFactory

    return RegionFactory(name="PK-Islamabad")


@pytest.fixture
def region_uk(db):
    from ralph.accounts.tests.factories import RegionFactory

    return RegionFactory(name="UK-London")


@pytest.fixture
def make_licence(db, region_pk):
    from ralph.licences.tests.factories import LicenceFactory

    def _make(number_bought=5, region=None, **kw):
        return LicenceFactory(number_bought=number_bought, region=region or region_pk, **kw)

    return _make


@pytest.fixture
def make_bo_asset(db, region_pk):
    from ralph.back_office.tests.factories import BackOfficeAssetFactory

    def _make(region=None, **kw):
        return BackOfficeAssetFactory(region=region or region_pk, **kw)

    return _make


@pytest.fixture
def make_user(db):
    from ralph.accounts.tests.factories import UserFactory

    def _make(**kw):
        return UserFactory(**kw)

    return _make
