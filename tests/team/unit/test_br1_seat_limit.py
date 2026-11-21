"""BR1 - Licence seat limit (boundary rule).

Rule (test basis): a licence has `number_bought` seats. Seats in use are the
sum of `quantity` over assignments to assets (BaseObjectLicence) and users
(LicenceUser). free = number_bought - used. An assignment must not make
used > number_bought, and must take at least 1 seat.

Ralph source: src/ralph/licences/models.py (Licence.used, Licence.free,
Licence.get_autocomplete_queryset) and BaseObjectLicence.clean.

3-point BVA on the limit (number_bought = 5, already used = 4, free = 1):
    request 0 seats -> below lower bound   -> reject
    request 1 seat  -> exactly at limit    -> accept
    request 2 seats -> just above limit    -> reject
"""
import pytest

pytestmark = [pytest.mark.django_db, pytest.mark.br1]


# ---------- used / free calculation (both code paths of Licence.used) ----------

def test_unsaved_licence_has_zero_used_and_free():
    from ralph.licences.models import Licence
    lic = Licence(number_bought=5)
    assert lic.used == 0          # branch: `if not self.pk`
    assert lic.free == 0          # branch: `if not self.pk`


def test_used_fallback_path_sums_assets_and_users(make_licence, make_bo_asset, make_user):
    from ralph.licences.models import BaseObjectLicence, Licence, LicenceUser
    lic = make_licence(number_bought=10)
    BaseObjectLicence.objects.create(licence=lic, base_object=make_bo_asset(), quantity=3)
    LicenceUser.objects.create(licence=lic, user=make_user(), quantity=2)
    fresh = Licence.objects.get(pk=lic.pk)          # plain manager -> AttributeError path
    assert fresh.used == 5
    assert fresh.free == 5


def test_used_fallback_path_with_no_assignments(make_licence):
    from ralph.licences.models import Licence
    lic = Licence.objects.get(pk=make_licence(number_bought=4).pk)
    assert lic.used == 0            # `or 0` when aggregate returns None
    assert lic.free == 4


def test_used_fast_path_uses_annotated_counts(make_licence, make_bo_asset, make_user):
    from ralph.licences.models import BaseObjectLicence, Licence, LicenceUser
    lic = make_licence(number_bought=6)
    BaseObjectLicence.objects.create(licence=lic, base_object=make_bo_asset(), quantity=1)
    LicenceUser.objects.create(licence=lic, user=make_user(), quantity=4)
    annotated = Licence.objects_used_free.get(pk=lic.pk)   # try path
    assert annotated.user_count == 4
    assert annotated.baseobject_count == 1
    assert annotated.used == 5
    assert annotated.free == 1


def test_used_fast_path_treats_null_counts_as_zero(make_licence):
    from ralph.licences.models import Licence
    lic = make_licence(number_bought=3)
    annotated = Licence.objects_used_free.get(pk=lic.pk)
    annotated.user_count = None          # force the `or 0` operand
    annotated.baseobject_count = None
    assert annotated.used == 0


# ---------- autocomplete only offers licences with free > 0 (BVA on 0) ----------

@pytest.mark.parametrize(
    "number_bought, assigned, offered",
    [
        (2, 1, True),    # free = 1  (just above 0) -> offered
        (2, 2, False),   # free = 0  (exactly 0)    -> hidden
        (2, 3, False),   # free = -1 (just below 0) -> hidden (over-assigned)
    ],
)
def test_autocomplete_boundary_on_free_seats(make_licence, make_bo_asset,
                                             number_bought, assigned, offered):
    from ralph.licences.models import BaseObjectLicence, Licence
    lic = make_licence(number_bought=number_bought)
    BaseObjectLicence.objects.create(licence=lic, base_object=make_bo_asset(), quantity=assigned)
    ids = set(Licence.get_autocomplete_queryset().values_list("pk", flat=True))
    assert (lic.pk in ids) is offered
