from datetime import timezone

from dateutil.parser import parse as parse_datetime
from django.conf import settings


def get_title(event_data):
    return event_data['issue']['fields']['summary']


def get_description(event_data):
    return event_data['issue']['fields']['description']


def get_ticket_id(event_data):
    return event_data['issue']['key']


def get_operation_status(event_data):
    from ralph.operations.models import OperationStatus

    status_conf = settings.CHANGE_MGMT_OPERATION_STATUSES
    status_map = {
        status_conf['OPENED']: OperationStatus.opened,
        status_conf['IN_PROGRESS']: OperationStatus.in_progress,
        status_conf['RESOLVED']: OperationStatus.resolved,
        status_conf['CLOSED']: OperationStatus.closed,
        status_conf['REOPENED']: OperationStatus.reopened,
        status_conf['TODO']: OperationStatus.todo,
        status_conf['BLOCKED']: OperationStatus.blocked
    }

    return status_map[event_data['issue']['fields']['status']['name']]


def get_operation_name(event_data):
    return event_data['issue']['fields']['issuetype']['name']


def get_assignee_username(event_data):
    try:
        return event_data['issue']['fields']['assignee']['key']
    except TypeError:
        # NOTE(romcheg): This means there is no assignee.
        return None


def get_creation_date(event_data):
    return _safe_load_datetime(event_data, 'created')


def get_last_update_date(event_data):
    return _safe_load_datetime(event_data, 'updated')


def get_resolution_date(event_data):
    return _safe_load_datetime(event_data, 'resolutiondate')


def _safe_load_datetime(event_data, field):
    """Safely serialize an ISO 8601 datetime string into a datetime object."""

    try:
        datetime_str = event_data['issue']['fields'][field]
        return parse_datetime(
            datetime_str
        ).astimezone(timezone.utc).replace(tzinfo=None)
    except:
        return None
