"""BR1 - seat limit ENFORCEMENT (defect SQE-D01).

These tests fail on the baseline commit and pass after
patch 0001-fix-sqe-d01-enforce-licence-seat-limit. They are added in the
fix PR together with the patch ("fails before, passes after").

3-point BVA on the limit (number_bought = 5, already used = 4, free = 1):
    request 0 seats -> below lower bound -> reject
    request 1 seat  -> exactly at limit  -> accept
    request 2 seats -> just above limit  -> reject
"""

import pytest
from django.core.exceptions import ValidationError

pytestmark = [pytest.mark.django_db, pytest.mark.br1]


# ---------- the limit itself on assignment (BVA 0 / 1 / 2 with free = 1) ----------
# Baseline Ralph does NOT enforce this (see defect SQE-D01). These tests fail
# on the baseline commit and pass after the fix PR.


def _licence_with_one_free_seat(make_licence, make_bo_asset):
    from ralph.licences.models import BaseObjectLicence

    lic = make_licence(number_bought=5)
    BaseObjectLicence.objects.create(licence=lic, base_object=make_bo_asset(), quantity=4)
    return lic


def test_assign_exactly_remaining_seat_is_accepted(make_licence, make_bo_asset):
    from ralph.licences.models import BaseObjectLicence

    lic = _licence_with_one_free_seat(make_licence, make_bo_asset)
    bol = BaseObjectLicence(licence=lic, base_object=make_bo_asset(), quantity=1)
    bol.clean()  # must not raise


def test_assign_more_than_free_seats_is_rejected(make_licence, make_bo_asset):
    from ralph.licences.models import BaseObjectLicence

    lic = _licence_with_one_free_seat(make_licence, make_bo_asset)
    bol = BaseObjectLicence(licence=lic, base_object=make_bo_asset(), quantity=2)
    with pytest.raises(ValidationError, match="free seat"):
        bol.clean()


def test_assign_zero_seats_is_rejected(make_licence, make_bo_asset):
    from ralph.licences.models import BaseObjectLicence

    lic = _licence_with_one_free_seat(make_licence, make_bo_asset)
    bol = BaseObjectLicence(licence=lic, base_object=make_bo_asset(), quantity=0)
    with pytest.raises(ValidationError, match="at least 1"):
        bol.clean()


def test_editing_existing_assignment_does_not_count_itself(make_licence, make_bo_asset):
    """Changing quantity 4 -> 5 on a 5-seat licence is allowed (own seats are reused)."""
    from ralph.licences.models import BaseObjectLicence

    lic = make_licence(number_bought=5)
    bol = BaseObjectLicence.objects.create(licence=lic, base_object=make_bo_asset(), quantity=4)
    bol.quantity = 5
    bol.clean()  # must not raise


# ---- from surviving-mutant analysis (ids 166, 173, 182, 186) ----


def test_zero_quantity_message_is_exact(make_licence, make_bo_asset):
    from ralph.licences.models import BaseObjectLicence

    bol = BaseObjectLicence(licence=make_licence(), base_object=make_bo_asset(), quantity=0)
    with pytest.raises(ValidationError) as exc:
        bol.clean()
    assert exc.value.messages == ["Quantity must be at least 1 seat."]


@pytest.mark.parametrize("used, requested, shown_free", [(4, 2, 1), (5, 1, 0), (6, 1, 0)])
def test_seat_error_message_reports_real_free_count(
    make_licence, make_bo_asset, used, requested, shown_free
):
    """free shown to the user never goes negative (over-assigned legacy data)."""
    from ralph.licences.models import BaseObjectLicence

    lic = make_licence(number_bought=5)
    BaseObjectLicence.objects.create(licence=lic, base_object=make_bo_asset(), quantity=used)
    bol = BaseObjectLicence(licence=lic, base_object=make_bo_asset(), quantity=requested)
    with pytest.raises(ValidationError) as exc:
        bol.clean()
    assert exc.value.messages == [
        f"Not enough free seats: requested {requested}, available {shown_free}."
    ]


# ---------- MT: seats held by USERS count against asset assignments (id 173) ----------


def test_user_held_seats_count_against_asset_assignment(make_licence, make_bo_asset, make_user):
    from ralph.licences.models import BaseObjectLicence, LicenceUser

    lic = make_licence(number_bought=5)
    LicenceUser.objects.create(licence=lic, user=make_user(), quantity=4)
    BaseObjectLicence(licence=lic, base_object=make_bo_asset(), quantity=1).clean()  # at limit
    with pytest.raises(ValidationError):
        BaseObjectLicence(licence=lic, base_object=make_bo_asset(), quantity=2).clean()
