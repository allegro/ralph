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

#from import_export import fields
#from import_export import resources
#from import_export import widgets
#from django.contrib.auth import get_user_model
#
#from ralph.assets.models import (
#    assets,
#    base,
#    components
#)
#from ralph.data_center.models import physical
#from ralph.data_center.models.components import (
#    DiskShare,
#    DiskShareMount
#)
#from ralph.data_importer.widgets import (
#    AssetServiceEnvWidget,
#    BaseObjectWidget
#)
#from ralph.back_office.models import (
#    BackOfficeAsset,
#    Warehouse
#)
#from ralph.licences.models import (
#    Licence,
#    LicenceAsset,
#    LicenceUser,
#    LicenceType,
#    SoftwareCategory
#)
#from ralph.supports.models import (
#    Support,
#    SupportType
#)
#
#
#class AssetModelResource(resources.ModelResource):
#    manufacturer = fields.Field(
#        column_name='manufacturer',
#        attribute='manufacturer',
#        widget=widgets.ForeignKeyWidget(assets.Manufacturer, 'name'),
#    )
#    category = fields.Field(
#        column_name='category',
#        attribute='category',
#        widget=widgets.ForeignKeyWidget(assets.Category, 'name'),
#    )
#
#    class Meta:
#        model = assets.AssetModel
#
#
#class GenericComponentResource(resources.ModelResource):
#    asset = fields.Field(
#        column_name='asset',
#        attribute='asset',
#        widget=BaseObjectWidget(base.BaseObject, 'sn')
#    )
#    model = fields.Field(
#        column_name='model',
#        attribute='model',
#        widget=widgets.ForeignKeyWidget(components.ComponentModel, 'name'),
#    )
#
#    class Meta:
#        model = components.GenericComponent
#
#
#class BackOfficeAssetResource(resources.ModelResource):
#    parent = fields.Field(
#        column_name='parent',
#        attribute='parent',
#        widget=widgets.ForeignKeyWidget(assets.Asset, 'sn'),
#    )
#    service_env = fields.Field(
#        column_name='service_env',
#        attribute='service_env',
#        widget=AssetServiceEnvWidget(assets.ServiceEnvironment, 'name')
#    )
#    model = fields.Field(
#        column_name='model',
#        attribute='model',
#        widget=widgets.ForeignKeyWidget(assets.AssetModel, 'name'),
#    )
#    user = fields.Field(
#        column_name='user',
#        attribute='user',
#        widget=widgets.ForeignKeyWidget(get_user_model(), 'username')
#    )
#    owner = fields.Field(
#        column_name='owner',
#        attribute='owner',
#        widget=widgets.ForeignKeyWidget(get_user_model(), 'username')
#    )
#    warehouse = fields.Field(
#        column_name='warehouse',
#        attribute='warehouse',
#        widget=widgets.ForeignKeyWidget(Warehouse, 'name'),
#    )
#
#    class Meta:
#        model = BackOfficeAsset
#
#
#class ServerRoomResource(resources.ModelResource):
#    data_center = fields.Field(
#        column_name='data_center',
#        attribute='data_center',
#        widget=widgets.ForeignKeyWidget(physical.DataCenter, 'name'),
#    )
#
#    class Meta:
#        model = physical.ServerRoom
#
#
#class RackResource(resources.ModelResource):
#    server_room = fields.Field(
#        column_name='server_room',
#        attribute='server_room',
#        widget=widgets.ForeignKeyWidget(physical.ServerRoom, 'name'),
#    )
#
#    class Meta:
#        model = physical.Rack
#
#
#class DataCenterAssetResource(resources.ModelResource):
#    parent = fields.Field(
#        column_name='parent',
#        attribute='parent',
#        widget=widgets.ForeignKeyWidget(assets.Asset, 'sn'),
#    )
#    service_env = fields.Field(
#        column_name='service_env',
#        attribute='service_env',
#        widget=AssetServiceEnvWidget(assets.ServiceEnvironment, 'name')
#    )
#    model = fields.Field(
#        column_name='model',
#        attribute='model',
#        widget=widgets.ForeignKeyWidget(assets.AssetModel, 'name'),
#    )
#    rack = fields.Field(
#        column_name='rack',
#        attribute='rack',
#        widget=widgets.ForeignKeyWidget(physical.Rack, 'name'),
#    )
#
#    class Meta:
#        model = physical.DataCenterAsset
#
#
#class ConnectionResource(resources.ModelResource):
#    outbound = fields.Field(
#        column_name='outbound',
#        attribute='outbound',
#        widget=widgets.ForeignKeyWidget(physical.DataCenterAsset, 'sn'),
#    )
#    inbound = fields.Field(
#        column_name='outbound',
#        attribute='outbound',
#        widget=widgets.ForeignKeyWidget(physical.DataCenterAsset, 'sn'),
#    )
#
#    class Meta:
#        model = physical.Connection
#
#
#class DiskShareResource(resources.ModelResource):
#    asset = fields.Field(
#        column_name='asset',
#        attribute='asset',
#        widget=BaseObjectWidget(base.BaseObject, 'sn')
#    )
#    model = fields.Field(
#        column_name='model',
#        attribute='model',
#        widget=widgets.ForeignKeyWidget(components.ComponentModel, 'name'),
#    )
#
#    class Meta:
#        model = DiskShare
#
#
#class DiskShareMountResource(resources.ModelResource):
#    share = fields.Field(
#        column_name='share',
#        attribute='share',
#        widget=widgets.ForeignKeyWidget(DiskShare, 'wwn'),
#    )
#    asset = fields.Field(
#        column_name='share',
#        attribute='share',
#        widget=widgets.ForeignKeyWidget(assets.Asset, 'sn'),
#    )
#
#    class Meta:
#        model = DiskShareMount
#
#
#class LicenceResource(resources.ModelResource):
#    manufacturer = fields.Field(
#        column_name='manufacturer',
#        attribute='manufacturer',
#        widget=widgets.ForeignKeyWidget(assets.Manufacturer, 'name'),
#    )
#    licence_type = fields.Field(
#        column_name='licence_type',
#        attribute='licence_type',
#        widget=widgets.ForeignKeyWidget(LicenceType, 'name'),
#    )
#    software_category = fields.Field(
#        column_name='software_category',
#        attribute='software_category',
#        widget=widgets.ForeignKeyWidget(SoftwareCategory, 'name'),
#    )
#
#    class Meta:
#        model = Licence
#
#
#class SupportResource(resources.ModelResource):
#    support_type = fields.Field(
#        column_name='support_type',
#        attribute='support_type',
#        widget=widgets.ForeignKeyWidget(SupportType, 'name'),
#    )
#
#    class Meta:
#        model = Support
#
#
#class ServiceEnvironmentResource(resources.ModelResource):
#    service = fields.Field(
#        column_name='service',
#        attribute='service',
#        widget=widgets.ForeignKeyWidget(assets.Service, 'name'),
#    )
#    environment = fields.Field(
#        column_name='environment',
#        attribute='environment',
#        widget=widgets.ForeignKeyWidget(assets.Environment, 'name'),
#    )
#
#    class Meta:
#        model = assets.ServiceEnvironment
#
#
#class LicenceAssetResource(resources.ModelResource):
#    licence = fields.Field(
#        column_name='licence',
#        attribute='licence',
#        widget=widgets.ForeignKeyWidget(Licence, 'niw'),
#    )
#    asset = fields.Field(
#        column_name='asset',
#        attribute='asset',
#        widget=widgets.ForeignKeyWidget(assets.Asset, 'sn'),
#    )
#
#    class Meta:
#        model = LicenceAsset
#
#
#class LicenceUserResource(resources.ModelResource):
#    licence = fields.Field(
#        column_name='licence',
#        attribute='licence',
#        widget=widgets.ForeignKeyWidget(Licence, 'niw'),
#    )
#    user = fields.Field(
#        column_name='user',
#        attribute='user',
#        widget=widgets.ForeignKeyWidget(get_user_model(), 'username')
#    )
#
#    class Meta:
#        model = LicenceUser
#
#
#class RackAccessoryResource(resources.ModelResource):
#    accessory = fields.Field(
#        column_name='accessory',
#        attribute='accessory',
#        widget=widgets.ForeignKeyWidget(physical.Accessory, 'name'),
#    )
#    rack = fields.Field(
#        column_name='rack',
#        attribute='rack',
#        widget=widgets.ForeignKeyWidget(physical.Rack, 'name'),
#    )
#
#    class Meta:
#        model = physical.RackAccessory
