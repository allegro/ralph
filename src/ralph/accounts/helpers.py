from functools import partial
from urllib.parse import urlencode

from django.conf import settings
from django.urls import reverse

from ralph.access_cards.models import AccessCard
from ralph.admin.sites import ralph_site
from ralph.back_office.models import BackOfficeAsset
from ralph.lib.transitions.models import Transition
from ralph.sim_cards.models import SIMCard

ACCEPTANCE_TRANSITION_ID = settings.ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG[
    "TRANSITION_ID"
]  # noqa
ACCEPTANCE_SIM_TRANSITION_ID = settings.ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG[
    "TRANSITION_SIM_ID"
]  # noqa
ACCEPTANCE_BACK_OFFICE_ACCEPT_STATUS = settings.ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG[
    "BACK_OFFICE_ACCEPT_STATUS"
]  # noqa
ACCEPTANCE_SIMCARD_ACCEPT_STATUS = settings.ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG[
    "SIMCARD_ACCEPT_STATUS"
]  # noqa
ACCEPTANCE_LOAN_TRANSITION_ID = settings.ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG[
    "LOAN_TRANSITION_ID"
]  # noqa
ACCEPTANCE_BACK_OFFICE_ACCEPT_LOAN_STATUS = (
    settings.ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG["BACK_OFFICE_ACCEPT_LOAN_STATUS"]
)  # noqa
ACCEPTANCE_RETURN_TRANSITION_ID = settings.ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG[
    "RETURN_TRANSITION_ID"
]  # noqa
ACCEPTANCE_BACK_OFFICE_RETURN_STATUS = settings.ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG[
    "BACK_OFFICE_ACCEPT_RETURN_STATUS"
]  # noqa
ACCEPTANCE_ACCESS_CARD_TRANSITION_ID = settings.ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG[
    "TRANSITION_ACCESS_CARD_ID"
]  # noqa
ACCEPTANCE_ACCESS_CARD_ACCEPT_STATUS = settings.ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG[
    "ACCESS_CARD_ACCEPT_ACCEPT_STATUS"
]  # noqa
ACCEPTANCE_BACK_OFFICE_TEAM_ACCEPT_STATUS = (
    settings.ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG["BACK_OFFICE_TEAM_ACCEPT_STATUS"]
)  # noqa
ACCEPTANCE_TEAM_ACCEPT_TRANSITION_ID = settings.ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG[
    "TRANSITION_TEAM_ACCEPT_ID"
]  # noqa
ACCEPTANCE_BACK_OFFICE_TEST_ACCEPT_STATUS = (
    settings.ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG["BACK_OFFICE_TEST_ACCEPT_STATUS"]
)  # noqa
ACCEPTANCE_TEST_ACCEPT_TRANSITION_ID = settings.ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG[
    "TRANSITION_TEST_ACCEPT_ID"
]  # noqa


def transition_exists(transition_id):
    return Transition.objects.filter(id=transition_id).exists()


acceptance_transition_exists = partial(transition_exists, ACCEPTANCE_TRANSITION_ID)
acceptance_sim_transition_exists = partial(
    transition_exists, ACCEPTANCE_SIM_TRANSITION_ID
)
loan_transition_exists = partial(transition_exists, ACCEPTANCE_LOAN_TRANSITION_ID)
acceptance_access_card_transition_exists = partial(
    transition_exists, ACCEPTANCE_ACCESS_CARD_TRANSITION_ID
)
acceptance_team_asset_transition_exists = partial(
    transition_exists, ACCEPTANCE_TEAM_ACCEPT_TRANSITION_ID
)
acceptance_test_asset_transition_exists = partial(
    transition_exists, ACCEPTANCE_TEST_ACCEPT_TRANSITION_ID
)


def get_assets(user, status):
    return BackOfficeAsset.objects.filter(status=status).filter(user=user)


def get_simcards(user, status):
    return SIMCard.objects.filter(status=status).filter(user=user)


def get_access_cards(user, status):
    return AccessCard.objects.filter(status=status, user=user)


get_assets_to_accept = partial(get_assets, status=ACCEPTANCE_BACK_OFFICE_ACCEPT_STATUS)
get_simcards_to_accept = partial(get_simcards, status=ACCEPTANCE_SIMCARD_ACCEPT_STATUS)
get_assets_to_accept_loan = partial(
    get_assets, status=ACCEPTANCE_BACK_OFFICE_ACCEPT_LOAN_STATUS
)
get_assets_to_accept_return = partial(
    get_assets, status=ACCEPTANCE_BACK_OFFICE_RETURN_STATUS
)
get_access_cards_to_accept = partial(
    get_access_cards, status=ACCEPTANCE_ACCESS_CARD_ACCEPT_STATUS
)
get_team_assets_to_accept = partial(
    get_assets, status=ACCEPTANCE_BACK_OFFICE_TEAM_ACCEPT_STATUS
)
get_test_assets_to_accept = partial(
    get_assets, status=ACCEPTANCE_BACK_OFFICE_TEST_ACCEPT_STATUS
)


def get_acceptance_url(user):
    assets_to_accept = get_assets_to_accept(user)
    admin_instance = ralph_site.get_admin_instance_for_model(BackOfficeAsset)
    url_name = admin_instance.get_transition_bulk_url_name()
    if assets_to_accept:
        url = reverse(url_name, args=(ACCEPTANCE_TRANSITION_ID,))
        query = urlencode([("select", a.id) for a in assets_to_accept])
        return "?".join((url, query))
    return None


def get_simcard_acceptance_url(user):
    assets_to_accept = get_simcards_to_accept(user)
    admin_instance = ralph_site.get_admin_instance_for_model(SIMCard)
    url_name = admin_instance.get_transition_bulk_url_name()
    if assets_to_accept:
        url = reverse(url_name, args=(ACCEPTANCE_SIM_TRANSITION_ID,))
        query = urlencode([("select", a.id) for a in assets_to_accept])
        return "?".join((url, query))
    return None


def get_loan_acceptance_url(user):
    assets_to_accept = get_assets_to_accept_loan(user)
    admin_instance = ralph_site.get_admin_instance_for_model(BackOfficeAsset)
    url_name = admin_instance.get_transition_bulk_url_name()
    if assets_to_accept:
        url = reverse(url_name, args=(ACCEPTANCE_LOAN_TRANSITION_ID,))
        query = urlencode([("select", a.id) for a in assets_to_accept])
        return "?".join((url, query))
    return None


def get_return_acceptance_url(user):
    assets_to_accept = get_assets_to_accept_return(user)
    admin_instance = ralph_site.get_admin_instance_for_model(BackOfficeAsset)
    url_name = admin_instance.get_transition_bulk_url_name()
    if assets_to_accept:
        url = reverse(url_name, args=(ACCEPTANCE_RETURN_TRANSITION_ID,))
        query = urlencode([("select", a.id) for a in assets_to_accept])
        return "?".join((url, query))
    return None


def get_access_card_acceptance_url(user):
    assets_to_accept = get_access_cards_to_accept(user)
    admin_instance = ralph_site.get_admin_instance_for_model(AccessCard)
    url_name = admin_instance.get_transition_bulk_url_name()
    if assets_to_accept:
        url = reverse(url_name, args=(ACCEPTANCE_ACCESS_CARD_TRANSITION_ID,))
        query = urlencode([("select", a.id) for a in assets_to_accept])
        return "?".join((url, query))
    return None


def get_team_asset_acceptance_url(user):
    assets_to_accept = get_team_assets_to_accept(user)
    admin_instance = ralph_site.get_admin_instance_for_model(BackOfficeAsset)
    url_name = admin_instance.get_transition_bulk_url_name()
    if assets_to_accept:
        url = reverse(url_name, args=(ACCEPTANCE_TEAM_ACCEPT_TRANSITION_ID,))
        query = urlencode([("select", a.id) for a in assets_to_accept])
        return "?".join((url, query))
    return None


def get_test_asset_acceptance_url(user):
    assets_to_accept = get_test_assets_to_accept(user)
    admin_instance = ralph_site.get_admin_instance_for_model(BackOfficeAsset)
    url_name = admin_instance.get_transition_bulk_url_name()
    if assets_to_accept:
        url = reverse(url_name, args=(ACCEPTANCE_TEST_ACCEPT_TRANSITION_ID,))
        query = urlencode([("select", a.id) for a in assets_to_accept])
        return "?".join((url, query))
    return None
