from typing import Type

from dj.choices import Choices
from import_export.fields import Field
from import_export.resources import ModelResource
from import_export.widgets import Widget

from ralph.data_center.models import (
    DataCenterAsset,
    Orientation,
    RackOrientation
)
from ralph.networks.models import IPAddress


class ChoiceWidget(Widget):

    def __init__(self, choice: Type[Choices]) -> None:
        self.choice = choice

    def render(self, value):
        if value:
            return self.choice.from_id(value).name
        else:
            return ''


class ReadonlyField(Field):

    def __init__(
        self, attribute=None, column_name=None, widget=None, default=None
    ):
        super().__init__(attribute, column_name, widget, default, False)


DATA_CENTER_ASSET_FIELDS = (
    'dc', 'server_room', 'rack', 'rack_orientation', 'orientation', 'position',
    'model', 'hostname', 'management_ip', 'ip', 'barcode', 'sn'
)


class DataCenterAssetTextResource(ModelResource):
    """
    DataCenterAsset resource with relations expressed in
    human friendly text form instead of database `id` field
    of the related object.
    """
    dc = ReadonlyField(
        attribute='rack__server_room__data_center__name'
    )
    server_room = ReadonlyField(
        attribute='rack__server_room__name'
    )
    rack = ReadonlyField(
        attribute='rack__name'
    )
    rack_orientation = ReadonlyField(
        attribute='rack__orientation',
        widget=ChoiceWidget(choice=RackOrientation)
    )
    orientation = ReadonlyField(
        attribute='orientation',
        widget=ChoiceWidget(choice=Orientation)
    )
    model = ReadonlyField(
        attribute='model__name'
    )
    management_ip = ReadonlyField(
        attribute='management_ip'
    )
    ip = ReadonlyField(
        attribute='ip'
    )

    class Meta:
        model = DataCenterAsset
        select_related = ('rack__server_room__data_center',)
        prefetch_related = ('ethernet_set__ipaddress',)
        fields = DATA_CENTER_ASSET_FIELDS
        export_order = DATA_CENTER_ASSET_FIELDS

    def _get_ip(self, dc_asset, is_management=True):
        if dc_asset:
            # find first management_ip here
            # notice that dc_asset.management_ip property could not be used
            # here, because it will omit prefetch_related cache
            for eth in dc_asset.ethernet_set.all():
                try:
                    if (
                            eth.ipaddress and
                            eth.ipaddress.is_management == is_management
                    ):
                        return eth.ipaddress
                except IPAddress.DoesNotExist:
                    pass

    def dehydrate_management_ip(self, dc_asset):
        return str(self._get_ip(dc_asset))

    def dehydrate_ip(self, dc_asset):
        return str(self._get_ip(dc_asset, is_management=False))
