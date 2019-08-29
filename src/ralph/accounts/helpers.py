from functools import partial
from urllib.parse import urlencode

from django.conf import settings
from django.core.urlresolvers import reverse

from ralph.admin.sites import ralph_site
from ralph.back_office.models import BackOfficeAsset
from ralph.lib.transitions.models import Transition
from ralph.sim_cards.models import SIMCard

ACCEPTANCE_TRANSITION_ID = settings.ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG['TRANSITION_ID']  # noqa: E509
ACCEPTANCE_SIM_TRANSITION_ID = settings.ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG['TRANSITION_SIM_ID']  # noqa: E509
ACCEPTANCE_BACK_OFFICE_ACCEPT_STATUS = settings.ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG['BACK_OFFICE_ACCEPT_STATUS']  # noqa: E509
ACCEPTANCE_SIMCARD_ACCEPT_STATUS = settings.ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG['SIMCARD_ACCEPT_STATUS']  # noqa: E509
ACCEPTANCE_LOAN_TRANSITION_ID = settings.ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG['LOAN_TRANSITION_ID']  # noqa: E509
ACCEPTANCE_BACK_OFFICE_ACCEPT_LOAN_STATUS = settings.ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG['BACK_OFFICE_ACCEPT_LOAN_STATUS']  # noqa: E509
ACCEPTANCE_RETURN_TRANSITION_ID = settings.ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG['RETURN_TRANSITION_ID']  # noqa: E509
ACCEPTANCE_BACK_OFFICE_RETURN_STATUS = settings.ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG['BACK_OFFICE_ACCEPT_RETURN_STATUS']  # noqa: E509


def transition_exists(transition_id):
    return Transition.objects.filter(
        id=transition_id
    ).exists()


acceptance_transition_exists = partial(
    transition_exists, ACCEPTANCE_TRANSITION_ID
)
acceptance_sim_transition_exists = partial(
    transition_exists, ACCEPTANCE_SIM_TRANSITION_ID
)
loan_transition_exists = partial(
    transition_exists, ACCEPTANCE_LOAN_TRANSITION_ID
)


def get_assets(user, status):
    return BackOfficeAsset.objects.filter(
        status=status
    ).filter(user=user)


def get_simcards(user, status):
    return SIMCard.objects.filter(
        status=status
    ).filter(user=user)

get_assets_to_accept = partial(
    get_assets, status=ACCEPTANCE_BACK_OFFICE_ACCEPT_STATUS
)

get_simcards_to_accept = partial(
    get_simcards, status=ACCEPTANCE_SIMCARD_ACCEPT_STATUS
)
get_assets_to_accept_loan = partial(
    get_assets, status=ACCEPTANCE_BACK_OFFICE_ACCEPT_LOAN_STATUS
)
get_assets_to_accept_return = partial(
    get_assets, status=ACCEPTANCE_BACK_OFFICE_RETURN_STATUS
)


def get_acceptance_url(user):
    assets_to_accept = get_assets_to_accept(user)
    admin_instance = ralph_site.get_admin_instance_for_model(
        BackOfficeAsset
    )
    url_name = admin_instance.get_transition_bulk_url_name()
    if assets_to_accept:
        url = reverse(url_name, args=(ACCEPTANCE_TRANSITION_ID,))
        query = urlencode([('select', a.id) for a in assets_to_accept])
        return '?'.join((url, query))
    return None


def get_simcard_acceptance_url(user):
    assets_to_accept = get_simcards_to_accept(user)
    admin_instance = ralph_site.get_admin_instance_for_model(
        SIMCard
    )
    url_name = admin_instance.get_transition_bulk_url_name()
    if assets_to_accept:
        url = reverse(url_name, args=(ACCEPTANCE_SIM_TRANSITION_ID,))
        query = urlencode([('select', a.id) for a in assets_to_accept])
        return '?'.join((url, query))
    return None


def get_loan_acceptance_url(user):
    assets_to_accept = get_assets_to_accept_loan(user)
    admin_instance = ralph_site.get_admin_instance_for_model(
        BackOfficeAsset
    )
    url_name = admin_instance.get_transition_bulk_url_name()
    if assets_to_accept:
        url = reverse(url_name, args=(ACCEPTANCE_LOAN_TRANSITION_ID,))
        query = urlencode([('select', a.id) for a in assets_to_accept])
        return '?'.join((url, query))
    return None


def get_return_acceptance_url(user):
    assets_to_accept = get_assets_to_accept_return(user)
    admin_instance = ralph_site.get_admin_instance_for_model(
        BackOfficeAsset
    )
    url_name = admin_instance.get_transition_bulk_url_name()
    if assets_to_accept:
        url = reverse(url_name, args=(ACCEPTANCE_RETURN_TRANSITION_ID,))
        query = urlencode([('select', a.id) for a in assets_to_accept])
        return '?'.join((url, query))
    return None
