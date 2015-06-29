# -*- coding: utf-8 -*-
"""
Models independent:

ralph importer AssetLastHostname file
ralph importer Environment file
ralph importer Service file
ralph importer Manufacturer file
ralph importer Category file
ralph importer ComponentModel file
ralph importer Warehouse file
ralph importer DataCenter file
ralph importer Accessory file
ralph importer Database file
ralph importer VIP file
ralph importer VirtualServer file
ralph importer CloudProject file
ralph importer LicenceType file
ralph importer SoftwareCategory ile
ralph importer SupportType file

Custom resoruces models
ralph.assets.models.assets.AssetModel
ralph.assets.models.components.GenericComponent
ralph.back_office.models.BackOfficeAsset
ralph.data_center.models.physical.ServerRoom
ralph.data_center.models.physical.Rack
ralph.data_center.models.physical.DataCenterAsset
ralph.data_center.models.physical.Connection
ralph.data_center.models.components.DiskShare
ralph.data_center.models.components.DiskShareMount
ralph.licences.models.Licence
ralph.supports.models.Support

ManyToMany Models.

ralph.assets.models.assets.ServiceEnvironment
    - service,
    - environment
ralph.licences.models.LicenceAsset
    - licence
    - asset
ralph.licences.models.LicenceUser
    - licence
    - user
ralph.data_center.models.physical.RackAccessory
    - accessory
    - rack
"""
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
    components,
)
from ralph.data_center.models import physical
from ralph.data_center.models.components import (
    DiskShare,
    DiskShareMount,
)
from ralph.data_importer.widgets import (
    AssetServiceEnvWidget,
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
    Licence,
    LicenceAsset,
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


class GenericComponentResource(ImportForeignKeyMixin, resources.ModelResource):
    asset = fields.Field(
        column_name='asset',
        attribute='asset',
        widget=BaseObjectWidget(base.BaseObject, 'sn'),
    )
    model = fields.Field(
        column_name='model',
        attribute='model',
        widget=ImportedForeignKeyWidget(components.ComponentModel),
    )

    class Meta:
        model = components.GenericComponent


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


class DataCenterAssetResource(ImportForeignKeyMixin, resources.ModelResource):
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


class DiskShareResource(ImportForeignKeyMixin, resources.ModelResource):
    asset = fields.Field(
        column_name='asset',
        attribute='asset',
        widget=BaseObjectWidget(base.BaseObject, 'sn'),
    )
    model = fields.Field(
        column_name='model',
        attribute='model',
        widget=ImportedForeignKeyWidget(components.ComponentModel),
    )

    class Meta:
        model = DiskShare


class DiskShareMountResource(ImportForeignKeyMixin, resources.ModelResource):
    share = fields.Field(
        column_name='share',
        attribute='share',
        widget=ImportedForeignKeyWidget(DiskShare),
    )
    asset = fields.Field(
        column_name='share',
        attribute='share',
        widget=ImportedForeignKeyWidget(assets.Asset),
    )

    class Meta:
        model = DiskShareMount


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


class SupportResource(ImportForeignKeyMixin, resources.ModelResource):
    support_type = fields.Field(
        column_name='support_type',
        attribute='support_type',
        widget=ImportedForeignKeyWidget(SupportType),
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


class LicenceAssetResource(ImportForeignKeyMixin, resources.ModelResource):
    licence = fields.Field(
        column_name='licence',
        attribute='licence',
        widget=ImportedForeignKeyWidget(Licence),
    )
    asset = fields.Field(
        column_name='asset',
        attribute='asset',
        widget=ImportedForeignKeyWidget(assets.Asset),
    )

    class Meta:
        model = LicenceAsset


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
