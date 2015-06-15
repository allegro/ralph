# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from import_export import fields
from import_export import resources
from ralph.discovery import models_device

from ralph.cmdb import models_ci
from ralph.discovery import models_component
from ralph_assets import models_assets


class BackOfficeAssetResource(resources.ModelResource):
    class Meta:
        fields = [
            'id',
            'barcode',
            'delivery_date',
            'deprecation_end_date',
            'deprecation_rate',
            'force_deprecation',
            'hostname',
            'invoice_date',
            'invoice_no',
            'loan_end_date',
            'model_id',
            'niw',
            'order_no',
            'price',
            'production_use_date',
            'production_year',
            'provider',
            'provider_order_date',
            'purchase_order',
            'request_date',
            'required_support',
            'sn',
            'source',
            'status',
            'task_url',
        ]
        model = models_assets.Asset

    def get_queryset(self):
        return self.Meta.model.objects.filter(
            type=models_assets.AssetType.back_office,
        )


class DataCenterAssetResource(resources.ModelResource):
    service_env = fields.Field()

    def dehydrate_hostname(self, asset):
        try:
            hostname = asset.device_info.ralph_device.name
        except AttributeError:
            hostname = None
        return hostname

    def dehydrate_rack(self, asset):
        try:
            rack = asset.device_info.rack.id
        except AttributeError:
            rack = None
        return rack

    def dehydrate_service_env(self, asset):
        device_environment = (
            asset.device_environment.name if asset.device_environment else ''
        )
        service = asset.service.name if asset.service else ''
        return "{}|{}".format(service, device_environment)

    class Meta:
        fields = (
            # to be skipped
            'id',
            #    'asset_ptr': '',
            #    'baseobject_ptr': '',
            # to be dehydrated
            'service_env',
            # TODO:
            #    'configuration_path': '',
            # complicated:
            # TODO:
            #    'parent': '',
            'barcode',
            # TODO: m2m
            'connections',
            'created',
            'delivery_date',
            'deprecation_end_date',
            'deprecation_rate',
            'force_deprecation',
            'invoice_date',
            'invoice_no',
            'loan_end_date',
            'model',
            'modified',
            'niw',
            'order_no',
            'orientation',
            'position',
            'price',
            'production_use_date',
            'production_year',
            'provider',
            'provider_order_date',
            'purchase_order',
            'rack',
            'remarks',
            'request_date',
            'required_support',
            'slot_no',
            'slots',
            'sn',
            'source',
            'status',
            'task_url',
            'hostname',
        )
        model = models_assets.Asset

    def get_queryset(self):
        return self.Meta.model.objects.filter(
            type=models_assets.AssetType.data_center
        )


class AssetModelResource(resources.ModelResource):
    class Meta:
        fields = (
            'id',
            'category',
            'cores_count',
            'height_of_device',
            'manufacturer',
            'power_consumption',
            'visualization_layout_back',
            'visualization_layout_front',
            # verify, these missing in old ralph
            # 'created': '',
            # 'modified': '',
            # 'name': '',
            # TODO: map it
            # 'type': '',
        )
        model = models_assets.AssetModel


class ManufacturerResource(resources.ModelResource):
    class Meta:
        model = models_assets.AssetManufacturer


class CategoryResource(resources.ModelResource):
    id = fields.Field('slug', column_name='id')

    def dehydrate_parent(self, asset_category):
        return asset_category.parent.slug if asset_category.parent else ''

    class Meta:
        fields = (
            'created datetime',
            'created_by_id',
            'modified',
            'modified_by_id',
            'slug',
            'name',
            'code',
            'is_blade',
            'parent',
            # skip it
            # cache_version
            # level
            # lft
            # rght
            # tree_id
            # type
        )
        model = models_assets.AssetCategory


class ServiceEnvironmentResource(resources.ModelResource):
    service = fields.Field()
    environment = fields.Field()

    def dehydrate_service(self, ci_relation):
        return ci_relation.parent.name

    def dehydrate_environment(self, ci_relation):
        return ci_relation.child.name

    def get_queryset(self):
        return models_ci.CIRelation.objects.filter(
            type=models_ci.CI_RELATION_TYPES.CONTAINS,
            parent__type=models_ci.CIType.objects.get(name='Service'),
            child__type=models_ci.CIType.objects.get(name='Environment'),
        )

    class Meta:
        fields = (
            'id',
            'service',
            'environment',
        )
        model = models_ci.CIRelation


class ServiceResource(resources.ModelResource):
    def dehydrate_environment(self, service):
        return service.child.name

    def dehydrate_profit_center(self, service):
        return service.parent.name

    def get_queryset(self):
        return models_ci.CIRelation.objects.filter(
            type=models_ci.CI_RELATION_TYPES.CONTAINS,
            parent__type=models_ci.CIType.objects.get(name='ProfitCenter'),
            child__type=models_ci.CIType.objects.get(name='Service'),
        )

    class Meta:
        fields = (
            'id',
            'name',
            'created',
            'modified',
            'profit_center',
            # TODO: no table in NG for now
            # 'cost_center': '',
        )
        model = models_ci.CIRelation


class EnvironmentResource(resources.ModelResource):
    class Meta:
        fields = ('id', 'name', 'created', 'modified',)
        model = models_device.DeviceEnvironment


class GenericComponentResource(resources.ModelResource):
    asset = fields.Field()

    def dehydrate_model(self, component):
        try:
            model_name = component.model.name
        except AttributeError:
            model_name = ''
        return model_name

    def dehydrate_asset(self, component):
        try:
            sn = component.device.get_asset().sn
        except AttributeError:
            sn = ''
        return sn

    class Meta:
        model = models_component.GenericComponent


class DiskShareResource(resources.ModelResource):
    def dehydrate_device(self, disk_share):
        try:
            value = disk_share.device.sn
        except AttributeError:
            value = ''
        return value

    def dehydrate_model(self, disk_share):
        try:
            value = disk_share.model.name
        except AttributeError:
            value = ''
        return value

    class Meta:
        model = models_component.DiskShare


class DiskShareMountResource(resources.ModelResource):
    def dehydrate_device(self, disk_share_mount):
        try:
            value = disk_share_mount.device.sn
        except AttributeError:
            value = ''
        return value

    def dehydrate_share(self, disk_share_mount):
        try:
            value = disk_share_mount.share.wwn
        except AttributeError:
            value = ''
        return value

    class Meta:
        model = models_component.DiskShareMount
