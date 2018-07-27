from functools import partial
from urllib.parse import urlencode

from django.conf import settings
from django.core.urlresolvers import reverse

from ralph.admin.sites import ralph_site
from ralph.back_office.models import BackOfficeAsset
from ralph.lib.transitions.models import Transition

ACCEPTANCE_TRANSITION_ID = settings.ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG['TRANSITION_ID']  # noqa: E509
ACCEPTANCE_BACK_OFFICE_ACCEPT_STATUS = settings.ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG['BACK_OFFICE_ACCEPT_STATUS']  # noqa: E509
ACCEPTANCE_LOAN_TRANSITION_ID = settings.ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG['LOAN_TRANSITION_ID']  # noqa: E509
ACCEPTANCE_BACK_OFFICE_ACCEPT_LOAN_STATUS = settings.ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG['BACK_OFFICE_ACCEPT_LOAN_STATUS']  # noqa: E509


def transition_exists(transition_id):
    return Transition.objects.filter(
        id=transition_id
    ).exists()


acceptance_transition_exists = partial(
    transition_exists, ACCEPTANCE_TRANSITION_ID
)
loan_transition_exists = partial(
    transition_exists, ACCEPTANCE_LOAN_TRANSITION_ID
)


def get_assets(user, status):
    return BackOfficeAsset.objects.filter(
        status=status
    ).filter(user=user)


get_assets_to_accept = partial(
    get_assets, status=ACCEPTANCE_BACK_OFFICE_ACCEPT_STATUS
)
get_assets_to_accept_loan = partial(
    get_assets,status=ACCEPTANCE_BACK_OFFICE_ACCEPT_LOAN_STATUS
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
