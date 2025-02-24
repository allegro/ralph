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


class ChoiceWidget(Widget):
    def __init__(self, choice: Type[Choices]) -> None:
        self.choice = choice

    def render(self, value, obj=None):
        if value:
            return self.choice.from_id(value).name
        else:
            return ""


class ReadonlyField(Field):
    def __init__(self, attribute=None, column_name=None, widget=None, default=None):
        super().__init__(attribute, column_name, widget, default, False)


DATA_CENTER_ASSET_FIELDS = (
    "dc",
    "server_room",
    "rack",
    "rack_orientation",
    "orientation",
    "position",
    "model",
    "hostname",
    "management_ip",
    "ip",
    "barcode",
    "sn",
)


class DataCenterAssetTextResource(ModelResource):
    """
    DataCenterAsset resource with relations expressed in
    human friendly text form instead of database `id` field
    of the related object.
    """

    dc = ReadonlyField(attribute="rack__server_room__data_center__name")
    server_room = ReadonlyField(attribute="rack__server_room__name")
    rack = ReadonlyField(attribute="rack__name")
    rack_orientation = ReadonlyField(
        attribute="rack__orientation", widget=ChoiceWidget(choice=RackOrientation)
    )
    orientation = ReadonlyField(
        attribute="orientation", widget=ChoiceWidget(choice=Orientation)
    )
    model = ReadonlyField(attribute="model__name")
    management_ip = ReadonlyField(attribute="management_ip")
    ip = ReadonlyField(attribute="ip")
    service_uid = ReadonlyField(attribute="service_env__service__uid")
    service = ReadonlyField(attribute="service_env__service")
    environment = ReadonlyField(attribute="service_env__environment")
    configuration_path = ReadonlyField(attribute="configuration_path")

    def get_queryset(self):
        return DataCenterAsset.objects.all().select_related(
            "service_env__service",
            "service_env__environment",
            "rack__server_room__data_center",
            "model",
            "configuration_path",
        )

    class Meta:
        model = DataCenterAsset
        fields = DATA_CENTER_ASSET_FIELDS
        export_order = DATA_CENTER_ASSET_FIELDS

    def _get_ip(self, dc_asset, is_management=True):
        # Due to multiple model inheritance, `prefetch_related` for
        # `ethernet_set` on DataCenterAsset does not work. For that reason,
        # a separate query will be issued here to fetch related `ethernet_set`.
        # To minimise the number of queries to the possible extent,
        # `select_related` for `ipaddress` field is used here.
        ethernet = (
            dc_asset.ethernet_set.select_related("ipaddress")
            .filter(ipaddress__is_management=is_management)
            .first()
        )
        return getattr(ethernet, "ipaddress", None)

    def dehydrate_management_ip(self, dc_asset):
        return str(self._get_ip(dc_asset))

    def dehydrate_ip(self, dc_asset):
        return str(self._get_ip(dc_asset, is_management=False))
