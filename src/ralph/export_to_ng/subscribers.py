import logging
from functools import wraps

from dateutil.parser import parse as dt_parse
from dj.choices import Choices
from pyhermes import subscriber

from ralph.discovery.admin import SAVE_PRIORITY
from ralph_assets.models import Asset, AssetModel
from ralph_assets.models_assets import AssetStatus, AssetType
from ralph_assets.models_dc_assets import DeviceInfo
from ralph_assets.views.utils import update_management_ip
from ralph.discovery.models import ServiceCatalog
from ralph.export_to_ng.publishers import publish_sync_ack_to_ralph3


logger = logging.getLogger(__name__)


class DataCenterAssetStatusRalphNG(Choices):
    _ = Choices.Choice

    new = _('new')
    used = _('in use')
    free = _('free')
    damaged = _('damaged')
    liquidated = _('liquidated')
    to_deploy = _('to deploy')

# mapping of Ralph NG statuses to Ralph2 statuses
DATA_CENTER_ASSET_STATUS_MAPPING = {
    DataCenterAssetStatusRalphNG.new.id: AssetStatus.new.id,
    DataCenterAssetStatusRalphNG.used.id: AssetStatus.used.id,
    DataCenterAssetStatusRalphNG.free.id: AssetStatus.free.id,
    DataCenterAssetStatusRalphNG.damaged.id: AssetStatus.damaged.id,
    DataCenterAssetStatusRalphNG.liquidated.id: AssetStatus.liquidated.id,
    DataCenterAssetStatusRalphNG.to_deploy.id: AssetStatus.to_deploy.id,
}


# TODO: turn off publisher for particular model(s) when in subscriber
# https://docs.djangoproject.com/en/1.9/topics/signals/#disconnecting-signals
# http://stackoverflow.com/questions/11487128/django-temporarily-disable-signals

class sync_subscriber(subscriber):
    """
    Log additional exception when sync has failed.
    """
    def _get_wrapper(self, func):
        @wraps(func)
        def exception_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except:
                logger.exception('Exception during syncing')
                raise
        return exception_wrapper


@sync_subscriber(topic='sync_dc_asset_to_ralph2')
def sync_dc_asset_to_ralph2_handler(data):
    """
    Saves asset data from Ralph3 to Ralph2.
    """
    creating = False
    if data['ralph2_id']:
        asset = Asset.objects.get(pk=data['ralph2_id'])
    else:
        asset = Asset(type=AssetType.data_center)
        creating = True
    device_info = asset.device_info if not creating else DeviceInfo

    # simple asset fields
    for field in [
        'source', 'invoice_no', 'provider', 'niw',
        'task_url', 'remarks', 'order_no', 'sn', 'barcode', 'price',
    ]:
        setattr(asset, field, data[field])

    device_info.position = data['position'] or None
    device_info.orientation = data['orientation']
    device_info.slot_no = data['slot_no']

    device_info.rack_id = data['rack']
    device_info.server_room_id = data['server_room']
    device_info.data_center_id = data['data_center']

    asset.invoice_date = data['invoice_date'] or None
    if asset.invoice_date:
        asset.invoice_date = dt_parse(asset.invoice_date)
    asset.deprecation_rate = data['depreciation_rate']
    asset.deprecation_end_date = data['depreciation_end_date'] or None
    if asset.deprecation_end_date:
        asset.deprecation_end_date = dt_parse(asset.deprecation_end_date)
    asset.force_deprecation = data['force_depreciation']

    asset.status = DATA_CENTER_ASSET_STATUS_MAPPING[int(data['status'])]

    # service-env
    asset.service = ServiceCatalog.objects.get(uid=data['service'])
    asset.device_environment_id = data['environment']

    # property_of
    asset.property_of_id = data['property_of'] or None

    # model
    asset.model_id = data['model'] or None

    # save
    device_info.save()
    if creating:
        asset.device_info = device_info
    asset.save()

    # mgmt
    update_management_ip(asset, data)

    publish_sync_ack_to_ralph3(asset, data['id'])

    # device part
    device = asset.get_ralph_device()
    device.name = data['hostname']
    device.save(priority=SAVE_PRIORITY)


@sync_subscriber(topic='sync_model_to_ralph2')
def sync_model_to_ralph2(data):
    """
    Saves asset model data from Ralph3 to Ralph2.
    """
    if data['ralph2_id']:
        model = AssetModel.objects.get(pk=data['ralph2_id'])
    else:
        model = AssetModel(type=AssetType.data_center)

    for field in [
        'cores_count', 'power_consumption', 'height_of_device', 'name'
    ]:
        setattr(model, field, data[field])

    model.manufacturer_id = data['manufacturer']
    model.category_id = data['category']
    model.save()
    publish_sync_ack_to_ralph3(model, data['id'])
