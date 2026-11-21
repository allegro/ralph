"""BR3 - Back Office asset status change (state transition rule).

Ralph stores allowed transitions in the database (Transition: name, source
statuses, target status, actions). Our test basis configures this lifecycle
for the licence workflows:

    T1 "release"   : {new, free}  -> in use      actions: assign_user, assign_licence
    T2 "return"    : {in use}     -> free        actions: unassign_user, unassign_licences
    T3 "liquidate" : {free, damaged} -> liquidated

Engine source: src/ralph/lib/transitions/models.py
    _check_instances_for_transition -> "wrong source status" if the asset's
    status is not in transition.source.

State transition coverage here (unit level): every allowed transition once
and at least one disallowed transition from each state used. The API/E2E
levels repeat the full table through HTTP.
"""
import pytest

pytestmark = [pytest.mark.django_db, pytest.mark.br3]


@pytest.fixture
def lifecycle(db):
    from ralph.back_office.models import BackOfficeAsset, BackOfficeAssetStatus as S
    from ralph.lib.transitions.models import Action, Transition, TransitionModel

    model = TransitionModel.get_for_field(BackOfficeAsset(), "status")

    def make(name, sources, target, actions):
        t = Transition.objects.create(
            name=name, model=model, source=[s.id for s in sources], target=target.id
        )
        for a in actions:
            act, _ = Action.objects.get_or_create(name=a)
            act.content_type.add(model.content_type)
            t.actions.add(act)
        return t

    return {
        "release": make("release", [S.new, S.free], S.used, ["assign_user", "assign_licence"]),
        "return": make("return", [S.used], S.free, ["unassign_user", "unassign_licences"]),
        "liquidate": make("liquidate", [S.free, S.damaged], S.liquidated, []),
    }


def _run(asset, transition, requester, data=None):
    from ralph.lib.transitions.models import run_field_transition
    return run_field_transition(
        instances=[asset], transition_obj_or_name=transition, field="status",
        requester=requester, data=data or {},
    )


def _status(asset):
    from ralph.back_office.models import BackOfficeAsset
    return BackOfficeAsset.objects.get(pk=asset.pk).status


# ---------------- allowed transitions ----------------

def test_release_new_asset_assigns_user_and_licence(lifecycle, make_bo_asset,
                                                    make_licence, make_user):
    from ralph.back_office.models import BackOfficeAssetStatus as S
    from ralph.licences.models import BaseObjectLicence, Licence
    asset = make_bo_asset(status=S.new)
    lic, user = make_licence(number_bought=3), make_user()
    ok, _ = _run(asset, lifecycle["release"], user, {
        "assign_user__user": user.pk,
        "assign_licence__licences": Licence.objects.filter(pk=lic.pk),
    })
    assert ok is True
    assert _status(asset) == S.used.id
    from ralph.back_office.models import BackOfficeAsset
    assert BackOfficeAsset.objects.get(pk=asset.pk).user_id == user.pk
    assert BaseObjectLicence.objects.filter(licence=lic, base_object=asset).count() == 1


def test_return_frees_asset_and_releases_licence_seats(lifecycle, make_bo_asset,
                                                       make_licence, make_user):
    from ralph.back_office.models import BackOfficeAssetStatus as S
    from ralph.licences.models import BaseObjectLicence, Licence
    user = make_user()
    asset = make_bo_asset(status=S.used, user=user)
    lic = make_licence(number_bought=3)
    BaseObjectLicence.objects.create(licence=lic, base_object=asset, quantity=1)
    ok, _ = _run(asset, lifecycle["return"], user)
    assert ok is True
    assert _status(asset) == S.free.id
    assert Licence.objects.get(pk=lic.pk).free == 3     # seat given back (shared record)


@pytest.mark.parametrize("source", ["free", "damaged"])
def test_liquidate_from_each_allowed_source(lifecycle, make_bo_asset, make_user, source):
    from ralph.back_office.models import BackOfficeAssetStatus as S
    asset = make_bo_asset(status=getattr(S, source))
    ok, _ = _run(asset, lifecycle["liquidate"], make_user())
    assert ok is True
    assert _status(asset) == S.liquidated.id


def test_release_from_free_state(lifecycle, make_bo_asset, make_licence, make_user):
    from ralph.back_office.models import BackOfficeAssetStatus as S
    from ralph.licences.models import Licence
    asset, user = make_bo_asset(status=S.free), make_user()
    ok, _ = _run(asset, lifecycle["release"], user, {
        "assign_user__user": user.pk,
        "assign_licence__licences": Licence.objects.none(),
    })
    assert ok is True and _status(asset) == S.used.id


# ---------------- disallowed transitions (one+ from each state) ----------------

@pytest.mark.parametrize(
    "state, transition",
    [
        ("new", "return"),          # new    -x-> free
        ("new", "liquidate"),       # new    -x-> liquidated
        ("used", "release"),        # in use -x-> in use
        ("used", "liquidate"),      # in use -x-> liquidated (must be returned first)
        ("free", "return"),         # free   -x-> free
        ("liquidated", "release"),  # terminal state
        ("liquidated", "return"),
        ("damaged", "release"),
    ],
)
def test_disallowed_transition_is_rejected_and_state_unchanged(
        lifecycle, make_bo_asset, make_user, state, transition):
    from ralph.back_office.models import BackOfficeAssetStatus as S
    from ralph.lib.transitions.exceptions import TransitionNotAllowedError
    asset = make_bo_asset(status=getattr(S, state))
    with pytest.raises(TransitionNotAllowedError) as exc:
        _run(asset, lifecycle[transition], make_user())
    assert "wrong source status" in str(exc.value.errors)
    assert _status(asset) == getattr(S, state).id


# ---------------- transition guards: preconditions and concurrency ----------------

def test_precondition_failure_blocks_transition(make_bo_asset, make_user):
    """Release-to-owner transition with `must_be_owner_of_asset`: a requester
    who is not the owner is rejected and the status is unchanged."""
    from ralph.back_office.models import BackOfficeAsset, BackOfficeAssetStatus as S
    from ralph.lib.transitions.exceptions import TransitionNotAllowedError
    from ralph.lib.transitions.models import Action, Transition, TransitionModel
    model = TransitionModel.get_for_field(BackOfficeAsset(), "status")
    t = Transition.objects.create(name="owner-release", model=model,
                                  source=[S.new.id], target=S.used.id)
    act, _ = Action.objects.get_or_create(name="must_be_owner_of_asset")
    act.content_type.add(model.content_type)
    t.actions.add(act)
    asset = make_bo_asset(status=S.new, owner=make_user())
    with pytest.raises(TransitionNotAllowedError) as exc:
        _run(asset, t, make_user())
    assert "requester is not an owner" in str(exc.value.errors)
    assert _status(asset) == S.new.id


@pytest.mark.parametrize("job_running, allowed", [(True, False), (False, True)])
def test_only_one_async_transition_at_a_time(lifecycle, make_bo_asset, make_user,
                                             job_running, allowed):
    """Repeated (double-clicked) async transition must not start twice."""
    from django.contrib.contenttypes.models import ContentType
    from ralph.back_office.models import BackOfficeAssetStatus as S
    from ralph.lib.external_services.models import JobStatus
    from ralph.lib.transitions.exceptions import TransitionNotAllowedError
    from ralph.lib.transitions.models import TransitionJob, _check_instances_for_transition
    t = lifecycle["liquidate"]
    t.run_asynchronously = True
    t.save()
    asset, user = make_bo_asset(status=S.free), make_user()
    TransitionJob.objects.create(
        service_name="ASYNC_TRANSITIONS", transition=t, object_id=asset.pk,
        content_type=ContentType.objects.get_for_model(asset),
        status=(JobStatus.STARTED if job_running else JobStatus.FINISHED).id,
    )
    if allowed:
        _check_instances_for_transition([asset], t, user)
    else:
        with pytest.raises(TransitionNotAllowedError, match="not allowed"):
            _check_instances_for_transition([asset], t, user)


def test_prepare_action_data_without_history_or_shared_params():
    from types import SimpleNamespace
    from ralph.lib.transitions.models import _prepare_action_data
    action = SimpleNamespace(name="assign_user")
    out = _prepare_action_data(action, {"assign_user__user": 7, "other__x": 1})
    assert out["user"] == 7
    assert "history_kwargs" not in out and "shared_params" not in out
