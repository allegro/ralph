import logging
from functools import wraps

from dateutil.parser import parse as dt_parse
from dj.choices import Choices
from django.conf import settings
from lck.django.common import nested_commit_on_success
from pyhermes import subscriber

from ralph.discovery.admin import SAVE_PRIORITY
from ralph_assets.models import Asset, AssetModel
from ralph_assets.models_assets import AssetStatus, AssetType, Warehouse, DataCenter
from ralph_assets.models_dc_assets import DeviceInfo
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


class sync_subscriber(subscriber):
    """
    Log additional exception when sync has failed.
    """
    def _get_wrapper(self, func):
        @wraps(func)
        @nested_commit_on_success
        def exception_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except:
                logger.exception('Exception during syncing')
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

    # simple asset fields
    for field in [
        'source', 'invoice_no', 'provider', 'niw',
        'task_url', 'remarks', 'order_no',
    ]:
        setattr(asset, field, data[field])

    asset.barcode = data['barcode'] or None
    asset.sn = data['sn'] or None

    asset.invoice_date = data['invoice_date'] or None
    if asset.invoice_date:
        asset.invoice_date = dt_parse(asset.invoice_date)
    asset.deprecation_rate = (
        data['depreciation_rate'] or settings.DEFAULT_DEPRECATION_RATE
    )
    asset.deprecation_end_date = data['depreciation_end_date'] or None
    if asset.deprecation_end_date:
        asset.deprecation_end_date = dt_parse(asset.deprecation_end_date)
    asset.force_deprecation = data['force_depreciation']
    asset.price = data['price'] or None

    asset.status = DATA_CENTER_ASSET_STATUS_MAPPING[int(data['status'])]

    # service-env
    asset.service = ServiceCatalog.objects.get(uid=data['service'])
    asset.device_environment_id = data['environment']

    # property_of
    asset.property_of_id = data['property_of'] or None

    # model
    asset.model_id = data['model'] or None

    # default value
    asset.region_id = 1  # from ralph/accounts/fixtures/initial_data.yaml

    # warehouse based on dc
    try:
        asset.warehouse = Warehouse.objects.get(
            name=DataCenter.objects.get(pk=data['data_center'])
        )
    except (Warehouse.DoesNotExist, DataCenter.DoesNotExist):
        asset.warehouse_id = settings.NG_SYNC_DEFAULT_WAREHOUSE

    if creating:
        device_info = DeviceInfo()
    else:
        device_info = asset.device_info

    device_info.position = data['position'] or None
    device_info.orientation = data['orientation']
    device_info.slot_no = data['slot_no']

    device_info.rack_id = data['rack']
    device_info.server_room_id = data['server_room']
    device_info.data_center_id = data['data_center']
    device_info._handle_post_save = False
    device_info.save()

    # save
    if creating:
        asset.device_info = device_info
    asset._handle_post_save = False
    asset.save()

    # device part
    device = asset.get_ralph_device()
    device.name = data['hostname']
    device.management_ip = data.get('management_ip')
    device._handle_post_save = False
    device.save(priority=SAVE_PRIORITY)

    publish_sync_ack_to_ralph3(asset, data['id'])


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
    model._handle_post_save = False
    model.save()
    publish_sync_ack_to_ralph3(model, data['id'])
