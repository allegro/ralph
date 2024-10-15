from collections import namedtuple

from django.conf import settings

from ralph.back_office.models import BackOfficeAssetStatus
from ralph.data_center.models import DataCenterAssetStatus

EmailContext = namedtuple("EmailContext", "from_email subject body")


def get_email_context_for_transition(transition_name: str) -> EmailContext:
    """Default method used in action (send_attachments_to_user)."""
    default = {
        "from_email": settings.EMAIL_FROM,
        "subject": "Documents for {}".format(transition_name),
        "body": 'Please see documents provided in attachments for "{}".'.format(
            transition_name
        ),  # noqa
    }
    return EmailContext(**default)


def _status_converter(old_status_id, target_status_id, from_status_cls, to_status_cls):
    """
    Convert BackOfficeAsset (BO) status to DatacenterAsset (DC) status (or the
    other way round).
    Try using status with the same name.
    If no status with such name exists, use name of the default status from
    transition.
    If no status with such name exists, use default status from settings.

    Args:
        old_status_id: BO status (int)
        target_status_id: ID of default status assigned to transition
        from_status_cls: Source status class
        to_status_cls: Destination status class

    Returns:
        new_status_id: DC status (int)
    """
    if not target_status_id:
        target_status_id = old_status_id
    source_status = from_status_cls.from_id(target_status_id)
    try:
        return to_status_cls.from_name(source_status.name).id
    except ValueError:
        if to_status_cls == DataCenterAssetStatus:
            return settings.CONVERT_TO_DATACENTER_ASSET_DEFAULT_STATUS_ID
        elif to_status_cls == BackOfficeAssetStatus:
            return settings.CONVERT_TO_BACKOFFICE_ASSET_DEFAULT_STATUS_ID


def bo_asset_to_dc_asset_status_converter(old_status_id, target_status_id):
    return _status_converter(
        old_status_id,
        target_status_id,
        from_status_cls=BackOfficeAssetStatus,
        to_status_cls=DataCenterAssetStatus,
    )


def dc_asset_to_bo_asset_status_converter(old_status_id, target_status_id):
    return _status_converter(
        old_status_id,
        target_status_id,
        from_status_cls=DataCenterAssetStatus,
        to_status_cls=BackOfficeAssetStatus,
    )
