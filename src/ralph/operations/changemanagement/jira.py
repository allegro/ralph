import logging
from datetime import timezone

from dateutil.parser import parse as parse_datetime

logger = logging.getLogger(__name__)


def get_title(event_data):
    return event_data["issue"]["fields"]["summary"]


def get_description(event_data):
    return event_data["issue"]["fields"]["description"]


def get_ticket_id(event_data):
    return event_data["issue"]["key"]


def get_operation_status(event_data):
    return event_data["issue"]["fields"]["status"]["name"]


def get_operation_name(event_data):
    return event_data["issue"]["fields"]["issuetype"]["name"]


def get_assignee_username(event_data):
    try:
        return event_data["issue"]["fields"]["assignee"]["key"]
    except TypeError:
        # NOTE(romcheg): This means there is no assignee.
        return None


def get_reporter_username(event_data):
    try:
        return event_data["issue"]["fields"]["reporter"]["key"]
    except TypeError:
        # NOTE(romcheg): This means the reporter is not specified.
        return None


def get_creation_date(event_data):
    return _safe_load_datetime(event_data, "created")


def get_last_update_date(event_data):
    return _safe_load_datetime(event_data, "updated")


def get_resolution_date(event_data):
    return _safe_load_datetime(event_data, "resolutiondate")


def _safe_load_datetime(event_data, field):
    """Safely serialize an ISO 8601 datetime string into a datetime object."""

    try:
        datetime_str = event_data["issue"]["fields"][field]
        return (
            parse_datetime(datetime_str).astimezone(timezone.utc).replace(tzinfo=None)
        )
    except:  # noqa
        return None
