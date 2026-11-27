"""SQE-D03 - the release transition's assign_licence action bypasses BR1/BR2.

BackOfficeAsset.assign_licence uses BaseObjectLicence.objects.get_or_create(),
which never calls clean(). Expected (test basis FR7, FR8): releasing an asset
with a licence from another region, or with a fully used licence, must not
create the assignment. Observed on baseline (and after fix D01): it does.
Strict xfail = documented open defect; turns red when fixed.
"""

import pytest

pytestmark = [pytest.mark.django_db, pytest.mark.br2]


def _release(asset, licence, user):
    from ralph.back_office.models import BackOfficeAsset, BackOfficeAssetStatus as S
    from ralph.lib.transitions.models import (
        Action,
        Transition,
        TransitionModel,
        run_field_transition,
    )
    from ralph.licences.models import Licence

    model = TransitionModel.get_for_field(BackOfficeAsset(), "status")
    t = Transition.objects.create(
        name="release-d03", model=model, source=[S.new.id], target=S.used.id
    )
    act, _ = Action.objects.get_or_create(name="assign_licence")
    act.content_type.add(model.content_type)
    t.actions.add(act)
    run_field_transition(
        [asset],
        t,
        "status",
        user,
        data={"assign_licence__licences": Licence.objects.filter(pk=licence.pk)},
    )


@pytest.mark.xfail(strict=True, reason="SQE-D03: transition skips region rule")
def test_release_with_other_region_licence_is_not_assigned(
    make_licence, make_bo_asset, make_user, region_pk, region_uk
):
    from ralph.back_office.models import BackOfficeAssetStatus as S
    from ralph.licences.models import BaseObjectLicence

    lic = make_licence(region=region_uk)
    asset = make_bo_asset(region=region_pk, status=S.new)
    _release(asset, lic, make_user())
    assert not BaseObjectLicence.objects.filter(licence=lic, base_object=asset).exists()


@pytest.mark.xfail(strict=True, reason="SQE-D03: transition skips seat limit")
def test_release_with_full_licence_is_not_assigned(make_licence, make_bo_asset, make_user):
    from ralph.back_office.models import BackOfficeAssetStatus as S
    from ralph.licences.models import BaseObjectLicence, Licence

    lic = make_licence(number_bought=1)
    BaseObjectLicence.objects.create(licence=lic, base_object=make_bo_asset(), quantity=1)
    asset = make_bo_asset(status=S.new)
    _release(asset, lic, make_user())
    assert Licence.objects.get(pk=lic.pk).free >= 0
