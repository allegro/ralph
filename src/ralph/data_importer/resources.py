# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from import_export import fields
from import_export import resources
from django.contrib.auth import get_user_model

from ralph.assets.models import (
    assets,
    base,
)
from ralph.data_center.models import networks
from ralph.data_center.models import physical
from ralph.data_importer.widgets import (
    AssetServiceEnvWidget,
    BaseObjectManyToManyWidget,
    BaseObjectWidget,
    ImportedForeignKeyWidget,
    UserWidget,
)
from ralph.data_importer.mixins import ImportForeignKeyMixin
from ralph.back_office.models import (
    BackOfficeAsset,
    Warehouse,
)
from ralph.licences.models import (
    BaseObjectLicence,
    Licence,
    LicenceUser,
    LicenceType,
    SoftwareCategory,
)
from ralph.supports.models import (
    Support,
    SupportType,
)


class DefaultResource(ImportForeignKeyMixin, resources.ModelResource):
    pass


class AssetModelResource(ImportForeignKeyMixin, resources.ModelResource):
    manufacturer = fields.Field(
        column_name='manufacturer',
        attribute='manufacturer',
        widget=ImportedForeignKeyWidget(assets.Manufacturer),
    )
    category = fields.Field(
        column_name='category',
        attribute='category',
        widget=ImportedForeignKeyWidget(assets.Category),
    )

    class Meta:
        model = assets.AssetModel


class CategoryResource(ImportForeignKeyMixin, resources.ModelResource):
    parent = fields.Field(
        column_name='parent',
        attribute='parent',
        widget=ImportedForeignKeyWidget(assets.Category),
    )

    class Meta:
        model = assets.Category


class BackOfficeAssetResource(ImportForeignKeyMixin, resources.ModelResource):
    parent = fields.Field(
        column_name='parent',
        attribute='parent',
        widget=ImportedForeignKeyWidget(assets.Asset),
    )
    service_env = fields.Field(
        column_name='service_env',
        attribute='service_env',
        widget=AssetServiceEnvWidget(assets.ServiceEnvironment, 'name'),
    )
    model = fields.Field(
        column_name='model',
        attribute='model',
        widget=ImportedForeignKeyWidget(assets.AssetModel),
    )
    user = fields.Field(
        column_name='user',
        attribute='user',
        widget=UserWidget(get_user_model()),
    )
    owner = fields.Field(
        column_name='owner',
        attribute='owner',
        widget=UserWidget(get_user_model()),
    )
    warehouse = fields.Field(
        column_name='warehouse',
        attribute='warehouse',
        widget=ImportedForeignKeyWidget(Warehouse),
    )

    class Meta:
        model = BackOfficeAsset


class ServerRoomResource(ImportForeignKeyMixin, resources.ModelResource):
    data_center = fields.Field(
        column_name='data_center',
        attribute='data_center',
        widget=ImportedForeignKeyWidget(physical.DataCenter),
    )

    class Meta:
        model = physical.ServerRoom


class RackResource(ImportForeignKeyMixin, resources.ModelResource):
    server_room = fields.Field(
        column_name='server_room',
        attribute='server_room',
        widget=ImportedForeignKeyWidget(physical.ServerRoom),
    )

    class Meta:
        model = physical.Rack


class NetworkResource(ImportForeignKeyMixin, resources.ModelResource):

    data_center = fields.Field(
        column_name='data_center',
        attribute='data_center',
        widget=ImportedForeignKeyWidget(physical.DataCenter),
    )

    network_environment = fields.Field(
        column_name='network_environment',
        attribute='network_environment',
        widget=ImportedForeignKeyWidget(networks.NetworkEnvironment),
    )

    kind = fields.Field(
        column_name='kind',
        attribute='kind',
        widget=ImportedForeignKeyWidget(networks.NetworkKind),
    )

    class Meta:
        model = networks.Network


class IPAddressResource(ImportForeignKeyMixin, resources.ModelResource):

    asset = fields.Field(
        column_name='asset',
        attribute='asset',
        widget=ImportedForeignKeyWidget(physical.DataCenterAsset),
    )

    network = fields.Field(
        column_name='network',
        attribute='network',
        widget=ImportedForeignKeyWidget(networks.Network),
    )

    class Meta:
        model = networks.IPAddress


class DataCenterAssetResource(ImportForeignKeyMixin, resources.ModelResource):
    parent = fields.Field(
        column_name='parent',
        attribute='parent',
        widget=ImportedForeignKeyWidget(physical.DataCenterAsset),
    )
    service_env = fields.Field(
        column_name='service_env',
        attribute='service_env',
        widget=AssetServiceEnvWidget(assets.ServiceEnvironment, 'name'),
    )
    model = fields.Field(
        column_name='model',
        attribute='model',
        widget=ImportedForeignKeyWidget(assets.AssetModel),
    )
    rack = fields.Field(
        column_name='rack',
        attribute='rack',
        widget=ImportedForeignKeyWidget(physical.Rack),
    )

    class Meta:
        model = physical.DataCenterAsset


class ConnectionResource(ImportForeignKeyMixin, resources.ModelResource):
    outbound = fields.Field(
        column_name='outbound',
        attribute='outbound',
        widget=ImportedForeignKeyWidget(physical.DataCenterAsset),
    )
    inbound = fields.Field(
        column_name='outbound',
        attribute='outbound',
        widget=ImportedForeignKeyWidget(physical.DataCenterAsset),
    )

    class Meta:
        model = physical.Connection


class LicenceResource(ImportForeignKeyMixin, resources.ModelResource):
    manufacturer = fields.Field(
        column_name='manufacturer',
        attribute='manufacturer',
        widget=ImportedForeignKeyWidget(assets.Manufacturer),
    )
    licence_type = fields.Field(
        column_name='licence_type',
        attribute='licence_type',
        widget=ImportedForeignKeyWidget(LicenceType),
    )
    software_category = fields.Field(
        column_name='software_category',
        attribute='software_category',
        widget=ImportedForeignKeyWidget(SoftwareCategory),
    )

    class Meta:
        model = Licence


class SupportTypeResource(ImportForeignKeyMixin, resources.ModelResource):

    class Meta:
        model = SupportType


class SupportResource(ImportForeignKeyMixin, resources.ModelResource):
    support_type = fields.Field(
        column_name='support_type',
        attribute='support_type',
        widget=ImportedForeignKeyWidget(SupportType),
    )
    base_objects = fields.Field(
        column_name='base_objects',
        attribute='base_objects',
        widget=BaseObjectManyToManyWidget(base.BaseObject),
    )

    class Meta:
        model = Support


class ServiceEnvironmentResource(
    ImportForeignKeyMixin, resources.ModelResource
):
    service = fields.Field(
        column_name='service',
        attribute='service',
        widget=ImportedForeignKeyWidget(assets.Service),
    )
    environment = fields.Field(
        column_name='environment',
        attribute='environment',
        widget=ImportedForeignKeyWidget(assets.Environment),
    )

    class Meta:
        model = assets.ServiceEnvironment


class BaseObjectLicenceResource(
    ImportForeignKeyMixin,
    resources.ModelResource,
):
    licence = fields.Field(
        column_name='licence',
        attribute='licence',
        widget=ImportedForeignKeyWidget(Licence),
    )
    base_object = fields.Field(
        column_name='base_object',
        attribute='base_object',
        widget=BaseObjectWidget(base.BaseObject),
    )

    class Meta:
        model = BaseObjectLicence


class LicenceUserResource(ImportForeignKeyMixin, resources.ModelResource):
    licence = fields.Field(
        column_name='licence',
        attribute='licence',
        widget=ImportedForeignKeyWidget(Licence),
    )
    user = fields.Field(
        column_name='user',
        attribute='user',
        widget=UserWidget(get_user_model()),
    )

    class Meta:
        model = LicenceUser


class RackAccessoryResource(ImportForeignKeyMixin, resources.ModelResource):
    accessory = fields.Field(
        column_name='accessory',
        attribute='accessory',
        widget=ImportedForeignKeyWidget(physical.Accessory),
    )
    rack = fields.Field(
        column_name='rack',
        attribute='rack',
        widget=ImportedForeignKeyWidget(physical.Rack),
    )

    class Meta:
        model = physical.RackAccessory
