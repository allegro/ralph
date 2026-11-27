"""Area 3b - failure-and-recovery test for the licence assignment write.

Scenario: POST /api/base-objects-licences/ assigns 1 seat. The database fails
AFTER the assignment row has been inserted (a post_save hook raises
OperationalError, as a dropped connection or deadlock would).

Test basis: Ralph has two safety nets - ATOMIC_REQUESTS=True (settings/base.py)
and ReversionHistoryAPISerializerMixin.save() wrapping every API save in
transaction.atomic() (api/serializers.py). Verified: with BOTH switched off this
test fails (the half-written row survives), so it really guards the rollback.

Expected:
  1. the failed request leaves NO assignment and the seat count unchanged
     (the half-finished write is rolled back);
  2. after the dependency recovers, retrying the same request succeeds;
  3. the final state has exactly ONE assignment and free seats reduced by 1
     (no duplicate from the failed attempt).
"""

import pytest
from django.db import OperationalError
from django.db.models.signals import post_save
from rest_framework.test import APIClient

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.br1]


@pytest.fixture
def api(make_user):
    client = APIClient()
    client.force_authenticate(make_user(is_superuser=True, is_staff=True))
    return client


@pytest.fixture
def flaky_db():
    """Fail the first assignment write after the INSERT, then recover."""
    from ralph.licences.models import BaseObjectLicence

    state = {"fail_next": True, "failures": 0}

    def explode(sender, instance, created, **kwargs):
        if created and state["fail_next"]:
            state["fail_next"] = False
            state["failures"] += 1
            raise OperationalError("simulated: database connection lost mid-write")

    post_save.connect(explode, sender=BaseObjectLicence, dispatch_uid="sqe-flaky")
    yield state
    post_save.disconnect(sender=BaseObjectLicence, dispatch_uid="sqe-flaky")


def test_failed_write_rolls_back_and_retry_creates_exactly_one(
    api, flaky_db, make_licence, make_bo_asset
):
    from ralph.licences.models import BaseObjectLicence, Licence

    lic = make_licence(number_bought=3)
    asset = make_bo_asset()
    payload = {"licence": lic.pk, "base_object": asset.pk, "quantity": 1}

    # 1. dependency fails mid-write
    with pytest.raises(OperationalError):
        api.post("/api/base-objects-licences/", payload, format="json")
    assert flaky_db["failures"] == 1
    assert BaseObjectLicence.objects.filter(licence=lic).count() == 0  # rolled back
    assert Licence.objects.get(pk=lic.pk).free == 3  # shared record unchanged

    # 2. dependency restored -> retry the identical request
    resp = api.post("/api/base-objects-licences/", payload, format="json")
    assert resp.status_code == 201, resp.content

    # 3. correct final state, no duplicate
    assert BaseObjectLicence.objects.filter(licence=lic, base_object=asset).count() == 1
    assert Licence.objects.get(pk=lic.pk).free == 2

    # a further identical retry is rejected, still one row
    again = api.post("/api/base-objects-licences/", payload, format="json")
    assert again.status_code == 400
    assert BaseObjectLicence.objects.filter(licence=lic, base_object=asset).count() == 1
