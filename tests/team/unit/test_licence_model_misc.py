"""Remaining statements of the licences business-logic module
(string forms used in the UI/API and factory helpers), so the
module reaches 100% statement and branch coverage."""

import pytest

pytestmark = pytest.mark.django_db


def test_licence_type_and_software_create_from_string():
    from ralph.licences.models import LicenceType, Software

    assert LicenceType.create_from_string("per user").name == "per user"
    sw = Software.create_from_string(1, "Office")
    assert (sw.asset_type, sw.name) == (1, "Office")


def test_string_representations(make_licence, make_bo_asset, make_user):
    from ralph.licences.models import BaseObjectLicence, Licence, LicenceUser

    lic = make_licence(number_bought=7)
    assert str(lic).startswith("7 x ")
    bol = BaseObjectLicence.objects.create(licence=lic, base_object=make_bo_asset(), quantity=2)
    lu = LicenceUser.objects.create(licence=lic, user=make_user(), quantity=1)
    assert str(bol).startswith("2 of ")
    assert str(lu).startswith("1 of ")
    fresh = Licence.objects.get(pk=lic.pk)
    assert "(4 free)" in fresh.autocomplete_str


def test_related_managers_prefetch(make_licence, make_bo_asset):
    from ralph.licences.models import BaseObjectLicence, Licence

    lic = make_licence()
    BaseObjectLicence.objects.create(licence=lic, base_object=make_bo_asset())
    got = Licence.objects_used_free_with_related.get(pk=lic.pk)
    assert len(got.baseobjectlicence_set.all()) == 1
    assert Licence.objects_with_related.filter(pk=lic.pk).exists()


@pytest.mark.xfail(
    strict=True,
    raises=AttributeError,
    reason="SQE-D02: Software.licences iterates itself "
    "('generator' object has no attribute 'all')",
)
def test_software_licences_property_lists_its_licences(make_licence):
    """Expected: iterating Software.licences yields the software's licences.
    Observed on baseline: AttributeError. Tracked as defect SQE-D02; strict
    xfail turns red automatically as soon as someone fixes it."""
    lic = make_licence()
    assert list(lic.software.licences) == [lic]
