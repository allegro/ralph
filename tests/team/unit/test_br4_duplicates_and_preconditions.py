"""BR4 - No duplicate assignment, and ownership preconditions for transitions.

(a) A licence can be assigned to the same asset / user only once
    (BaseObjectLicence / LicenceUser unique_together). Re-running the
    assign_licence transition action must not create a second row
    (get_or_create) -> "repeated request, no duplicates".

(b) Precondition decisions used by asset-release transitions
    (src/ralph/back_office/models.py):

    _check_assets_owner: requester given? AND instance.owner == requester?
    _check_assets_user : requester given? AND instance.user  == requester?
    _check_user_assigned: instance.user set?
    autocomplete_user  : one distinct user AND that user is not None
"""
import pytest
from django.db import IntegrityError, transaction

pytestmark = [pytest.mark.django_db, pytest.mark.br4]


# ---------------- (a) duplicates ----------------

def test_same_licence_twice_on_same_asset_is_rejected_by_db(make_licence, make_bo_asset):
    from ralph.licences.models import BaseObjectLicence
    lic, asset = make_licence(), make_bo_asset()
    BaseObjectLicence.objects.create(licence=lic, base_object=asset)
    with pytest.raises(IntegrityError), transaction.atomic():
        BaseObjectLicence.objects.create(licence=lic, base_object=asset)


def test_same_licence_twice_on_same_user_is_rejected_by_db(make_licence, make_user):
    from ralph.licences.models import LicenceUser
    lic, user = make_licence(), make_user()
    LicenceUser.objects.create(licence=lic, user=user)
    with pytest.raises(IntegrityError), transaction.atomic():
        LicenceUser.objects.create(licence=lic, user=user)


def test_assign_licence_action_is_idempotent(make_licence, make_bo_asset):
    from ralph.back_office.models import BackOfficeAsset
    from ralph.licences.models import BaseObjectLicence
    lic, asset = make_licence(), make_bo_asset()
    for _ in range(3):                                   # repeated request
        BackOfficeAsset.assign_licence(instances=[asset], licences=[lic])
    assert BaseObjectLicence.objects.filter(licence=lic, base_object=asset).count() == 1


def test_unassign_licences_removes_all_rows_for_asset(make_licence, make_bo_asset):
    from ralph.back_office.models import BackOfficeAsset
    from ralph.licences.models import BaseObjectLicence
    asset = make_bo_asset()
    BackOfficeAsset.assign_licence(instances=[asset], licences=[make_licence(), make_licence()])
    BackOfficeAsset.unassign_licences(instances=[asset])
    assert not BaseObjectLicence.objects.filter(base_object=asset).exists()


# ---------------- (b) precondition decisions (decision tables) ----------------
# Decision table for _check_assets_owner / _check_assets_user
#   R1: requester missing             -> error "__all__"
#   R2: requester given, is owner     -> no error
#   R3: requester given, not owner    -> error for that instance

@pytest.mark.parametrize("fn_name, attr", [("_check_assets_owner", "owner"),
                                           ("_check_assets_user", "user")])
def test_precondition_r1_requester_missing(fn_name, attr, make_bo_asset):
    from ralph.back_office import models as bo
    errors = getattr(bo, fn_name)([make_bo_asset()])
    assert "__all__" in errors


@pytest.mark.parametrize("fn_name, attr", [("_check_assets_owner", "owner"),
                                           ("_check_assets_user", "user")])
def test_precondition_r2_requester_matches(fn_name, attr, make_bo_asset, make_user):
    from ralph.back_office import models as bo
    me = make_user()
    asset = make_bo_asset(**{attr: me})
    assert getattr(bo, fn_name)([asset], requester=me) == {}


@pytest.mark.parametrize("fn_name, attr", [("_check_assets_owner", "owner"),
                                           ("_check_assets_user", "user")])
def test_precondition_r3_requester_differs(fn_name, attr, make_bo_asset, make_user):
    from ralph.back_office import models as bo
    me, other = make_user(), make_user()
    asset = make_bo_asset(**{attr: other})
    errors = getattr(bo, fn_name)([asset], requester=me)
    assert asset in errors


def test_check_user_assigned_both_outcomes(make_bo_asset, make_user):
    from ralph.back_office.models import _check_user_assigned
    with_user = make_bo_asset(user=make_user())
    without = make_bo_asset(user=None)
    errors = _check_user_assigned([with_user, without])
    assert without in errors and with_user not in errors


# autocomplete_user: condition X = single distinct value, Y = value not None
#   X=T,Y=T -> pk string | X=T,Y=F -> None | X=F -> None
def test_autocomplete_user_single_user(make_bo_asset, make_user):
    from ralph.back_office.models import autocomplete_user
    u = make_user()
    assert autocomplete_user([], [make_bo_asset(user=u), make_bo_asset(user=u)]) == str(u.pk)


def test_autocomplete_user_all_empty(make_bo_asset):
    from ralph.back_office.models import autocomplete_user
    assert autocomplete_user([], [make_bo_asset(user=None)]) is None


def test_autocomplete_user_mixed_users(make_bo_asset, make_user):
    from ralph.back_office.models import autocomplete_user
    objs = [make_bo_asset(user=make_user()), make_bo_asset(user=make_user())]
    assert autocomplete_user([], objs) is None
