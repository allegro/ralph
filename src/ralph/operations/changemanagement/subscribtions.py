import pyhermes
from django.db import transaction
from django.contrib.auth import get_user_model
from django.conf import settings
from importlib import import_module


def _safe_load_user(username):
    """Loads an existing user or creates a new one."""

    if username is None:
        return

    model = get_user_model()

    user, created = model.objects.get_or_create(username=username)

    if created:
        user.is_active = False
        user.save()

    return user


def _safe_load_operation_type(operation_name):
    """Load operation type by its name. None, if not found."""
    from ralph.operations.models import OperationType

    try:
        return OperationType.objects.get(name=operation_name)
    except OperationType.DoesNotExits:
        return None


def _load_base_objects(object_ids):
    """Load base objects with the specified ids. [] if none is found."""

    from ralph.assets.models import BaseObject

    return BaseObject.objects.filter(id__in=object_ids)


@transaction.atomic
def record_operation(title, status, description, operation_name, ticket_id,
                     assignee_username=None, created_date=None,
                     update_date=None, resolution_date=None, bo_ids=None):

    from ralph.operations.models import Operation

    operation_type = _safe_load_operation_type(operation_name)

    operation, _ = Operation.objects.update_or_create(
        ticket_id=ticket_id,
        defaults=dict(
            title=title,
            description=description,
            status=status,
            type=operation_type,
            asignee=_safe_load_user(assignee_username),
            created_date=created_date,
            update_date=update_date,
            resolved_date=resolution_date
        )
    )

    if bo_ids:
        operation.base_objects = _load_base_objects(bo_ids)
        operation.save()


@pyhermes.subscriber(topic=settings.HERMES_CHANGE_MGMT_TOPICS['CHANGES'])
def receive_chm_event(event_data):
    """Process messages from the change management system."""
    try:
        change_processor = import_module(settings.CHANGE_MGMT_PROCESSOR)

        bo_ids = None
        if settings.CHANGE_MGMT_BO_LOADER:
            bo_loader = import_module(settings.CHANGE_MGMT_BO_LOADER)
            bo_ids = bo_loader.get_baseobjects_ids(event_data)

        record_operation(
            title=change_processor.get_title(event_data),
            description=change_processor.get_description(event_data),
            ticket_id=change_processor.get_ticket_id(event_data),
            status=change_processor.get_operation_status(event_data),
            operation_name=change_processor.get_operation_name(event_data),
            assignee_username=change_processor.get_assignee_username(
                event_data
            ),
            created_date=change_processor.get_creation_date(event_data),
            update_date=change_processor.get_last_update_date(event_data),
            resolution_date=change_processor.get_resolution_date(event_data),
            bo_ids=bo_ids
        )

    except Exception as e:
        # TODO(romcheg): Change this for something sensible
        raise
