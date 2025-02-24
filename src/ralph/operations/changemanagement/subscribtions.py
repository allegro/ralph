import logging
from importlib import import_module

import pyhermes
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction

from ralph.assets.models import BaseObject
from ralph.operations.changemanagement.exceptions import IgnoreOperation
from ralph.operations.models import Operation, OperationStatus, OperationType

logger = logging.getLogger(__name__)


change_processor = import_module(settings.CHANGE_MGMT_PROCESSOR)
base_object_loader = None

if settings.CHANGE_MGMT_BASE_OBJECT_LOADER:
    base_object_loader = import_module(settings.CHANGE_MGMT_BASE_OBJECT_LOADER)


def _safe_load_user(username):
    """Loads an existing user or creates a new one."""

    if username is None:
        return

    model = get_user_model()

    user, _ = model.objects.get_or_create(
        username=username, defaults={"is_active": False}
    )

    return user


def _safe_load_operation_type(operation_name):
    """Load operation type by its name. None, if not found."""

    try:
        return OperationType.objects.get(name=operation_name)
    except OperationType.DoesNotExist:
        return None


def _safe_load_status(status_name):
    """Load operation status by its name. None, if not found."""
    status, created = OperationStatus.objects.get_or_create(name=status_name)

    if created:
        logger.warning("Received an operation with a new status %s.", status_name)

    return status


def _load_base_objects(object_ids):
    """Load base objects with the specified ids. [] if none is found."""

    return BaseObject.objects.filter(id__in=object_ids)


@transaction.atomic
def record_operation(
    title,
    status_name,
    description,
    operation_name,
    ticket_id,
    assignee_username=None,
    reporter_username=None,
    created_date=None,
    update_date=None,
    resolution_date=None,
    base_object_ids=None,
):
    operation_type = _safe_load_operation_type(operation_name)

    # NOTE(romcheg): Changes of an unknown type should not be recorded.
    if operation_type is None:
        logger.warning(
            "Not recording operation with the " "unknown type: %s.", operation_name
        )
        return

    operation, _ = Operation.objects.update_or_create(
        ticket_id=ticket_id,
        defaults=dict(
            title=title,
            description=description,
            status=_safe_load_status(status_name),
            type=operation_type,
            assignee=_safe_load_user(assignee_username),
            reporter=_safe_load_user(reporter_username),
            created_date=created_date,
            update_date=update_date,
            resolved_date=resolution_date,
        ),
    )

    if base_object_ids:
        operation.base_objects = _load_base_objects(base_object_ids)
        operation.save()


@pyhermes.subscriber(topic=settings.HERMES_CHANGE_MGMT_TOPICS["CHANGES"])
def receive_chm_event(event_data):
    """Process messages from the change management system."""
    try:
        record_operation(
            title=change_processor.get_title(event_data),
            description=change_processor.get_description(event_data),
            ticket_id=change_processor.get_ticket_id(event_data),
            status_name=change_processor.get_operation_status(event_data),
            operation_name=change_processor.get_operation_name(event_data),
            assignee_username=change_processor.get_assignee_username(event_data),
            reporter_username=change_processor.get_reporter_username(event_data),
            created_date=change_processor.get_creation_date(event_data),
            update_date=change_processor.get_last_update_date(event_data),
            resolution_date=change_processor.get_resolution_date(event_data),
            base_object_ids=(
                base_object_loader.get_baseobjects_ids(event_data)
                if base_object_loader is not None
                else None
            ),
        )
    except IgnoreOperation as e:
        logger.warning(e.message)
    except Exception as e:
        logger.exception(
            "Encountered an unexpected failure while handling a change "
            "management event.",
            exc_info=e,
        )
