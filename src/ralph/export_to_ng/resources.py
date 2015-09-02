# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import os
from itertools import chain

from django.conf import settings
from django.db.models import Q
from import_export import fields
from import_export import resources

from ralph.account.models import Region
from ralph.cmdb import models_ci
from ralph.discovery import models_component
from ralph.discovery import models_device
from ralph.discovery import models_network
from ralph_assets import models_assets
from ralph_assets import models_dc_assets
from ralph_assets import models_support
from ralph_assets.licences.models import (
    Licence,
    LicenceAsset,
)


logger = logging.getLogger(__name__)


class AssetResource(resources.ModelResource):
    deprecation_end_date = fields.Field(
        'deprecation_end_date', column_name='depreciation_end_date'
    )
    deprecation_rate = fields.Field(
        'deprecation_rate', column_name='depreciation_rate'
    )
    force_deprecation = fields.Field(
        'force_deprecation', column_name='force_depreciation'
    )


class BackOfficeAssetResource(AssetResource):

    imei = fields.Field('imei', column_name='imei')

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
            'model',
            'niw',
            'order_no',
            'price',
            'production_use_date',
            'production_year',
            'provider',
            'provider_order_date',
            'purchase_order',
            'region',
            'request_date',
            'required_support',
            'sn',
            'source',
            'status',
            'task_url',
            'imei',
            'warehouse',
            'owner',
            'user',
            'remarks',
            'service_env',
        ]
        model = models_assets.Asset

    def get_queryset(self):
        return self.Meta.model.objects.filter(
            type=models_assets.AssetType.back_office,
            part_info=None,
        ).select_related('office_info')

    def dehydrate_imei(self, asset):
        try:
            imei = asset.office_info.imei or ''
        except AttributeError:
            imei = ''
        return imei

    def dehydrate_barcode(self, asset):
        return asset.barcode or ''

    def dehydrate_sn(self, asset):
        return asset.sn or ''

    def dehydrate_user(self, asset):
        try:
            username = asset.user.username or ''
        except AttributeError:
            username = ''
        return username

    def dehydrate_owner(self, asset):
        try:
            username = asset.owner.username or ''
        except AttributeError:
            username = ''
        return username

    def dehydrate_hostname(self, asset):
        try:
            hostname = asset.hostname or ''
        except AttributeError:
            hostname = ''
        return hostname

    def dehydrate_service_env(self, asset):
        service_env = ""
        service = getattr(asset.service, 'name', '')
        device_environment = getattr(asset.device_environment, 'name', '')
        if service and device_environment:
            service_env = "{}|{}".format(service, device_environment)
        return service_env


class DataCenterAssetResource(AssetResource):
    service_env = fields.Field()
    parent = fields.Field('parent', column_name='parent')
    rack = fields.Field('rack', column_name='rack')
    orientation = fields.Field('orientation', column_name='orientation')
    position = fields.Field('position', column_name='position')
    slot_no = fields.Field('slot_no', column_name='slot_no')

    def dehydrate_parent(self, asset):
        if (
            not asset.model.category.is_blade or
            not asset.device_info.position or
            not asset.device_info.rack
        ):
            return ''
        parents = models_assets.Asset.objects.select_related(
            'device_info',
        ).filter(
            Q(device_info__slot_no__isnull=True) | Q(device_info__slot_no=''),
            type=models_assets.AssetType.data_center,
            model__category__is_blade=False,
            part_info=None,
            device_info__rack=asset.device_info.rack,
            device_info__position=asset.device_info.position,
            model__category__slug__in=[
                '2-2-2-data-center-device-chassis-blade',
            ]
        ).exclude(
            device_info__rack__in=settings.NG_EXPORTER['rack_ids_where_parents_are_disallowed'],  # noqa
        )
        parents_ids = parents.values_list('id', flat=True)
        if len(parents_ids) == 0:
            parent = ''
        elif len(parents_ids) == 1:
            parent = parents_ids[0] or ''
        else:
            parents_msges = [
                "id, model, rack = {}, {}, {}".format(
                    p.model.name, p.id, p.device_info.rack,
                ) for p in parents
            ]
            msg = 'Found more then 1 parent:\n{}'.format(
                os.linesep.join(parents_msges)
            )
            logger.warning(msg)
            parent = ''
        return parent

    def dehydrate_rack(self, asset):
        try:
            rack = asset.device_info.rack.id or ''
        except AttributeError:
            rack = ''
        return rack

    def dehydrate_orientation(self, asset):
        try:
            orientation = asset.device_info.orientation or ''
        except AttributeError:
            orientation = ''
        return orientation

    def dehydrate_position(self, asset):
        try:
            position = asset.device_info.position or ''
        except AttributeError:
            position = ''
        return position

    def dehydrate_slot_no(self, asset):
        try:
            slot_no = asset.device_info.slot_no or ''
        except AttributeError:
            slot_no = ''
        return slot_no

    def dehydrate_barcode(self, asset):
        return asset.barcode or ''

    def dehydrate_sn(self, asset):
        return asset.sn or ''

    def dehydrate_hostname(self, asset):
        try:
            hostname = asset.device_info.ralph_device.name or ''
        except AttributeError:
            hostname = ''
        return hostname

    def dehydrate_service_env(self, asset):
        service_env = ""
        service = getattr(asset.service, 'name', '')
        device_environment = getattr(asset.device_environment, 'name', '')
        if service and device_environment:
            service_env = "{}|{}".format(service, device_environment)
        return service_env

    class Meta:
        fields = (
            # to be skipped
            'parent',
            'id',
            'service_env',
            # TODO:
            #    'configuration_path': '',
            'barcode',
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
        parents = self.Meta.model.objects.filter(
            Q(device_info__slot_no__isnull=True) | Q(device_info__slot_no=''),
            type=models_assets.AssetType.data_center,
            model__category__is_blade=False,
            part_info=None,
        )
        children = self.Meta.model.objects.filter(
            type=models_assets.AssetType.data_center,
            model__category__is_blade=True,
            part_info=None,
        )
        return list(chain(parents, children))


class NetworkResource(resources.ModelResource):
    kind = fields.Field('kind', column_name='kind')

    def dehydrate_kind(self, network):
        return network.kind_id or ''

    def dehydrate_network_environment(self, network):
        return network.environment_id or ''

    class Meta:
        fields = (
            'id',
            'name',
            'created',
            'modified',
            'address',
            'gateway',
            'gateway_as_int',
            'reserved',
            'reserved_top_margin',
            'remarks',
            'vlan',
            'min_ip',
            'max_ip',
            'ignore_addresses',
            'dhcp_broadcast',
            'dhcp_config',
            'kind',
        )
        model = models_network.Network


class IPAddressResource(resources.ModelResource):
    asset = fields.Field('asset', column_name='asset')
    network = fields.Field('network', column_name='network')

    def dehydrate_asset(self, ip_address):
        try:
            asset_id = ip_address.device.get_asset().id or ''
        except AttributeError:
            asset_id = ''
        return asset_id

    def dehydrate_network(self, ip_address):
        return ip_address.network_id or ''

    class Meta:
        fields = (
            'id',
            'created',
            'modified',
            'last_seen',
            'address',
            'number',
            'hostname',
            'is_management',
            'is_public',
            'asset',
            'network',
        )
        model = models_network.IPAddress


class AssetModelResource(resources.ModelResource):
    has_parent = fields.Field('has_parent', column_name='has_parent')

    def dehydrate_has_parent(self, asset_model):
        try:
            has_parent = asset_model.category.is_blade
        except AttributeError:
            has_parent = False
        return int(has_parent)

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
            'type',
            'created',
            'modified',
            'name',
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
        return ci_relation.parent.id

    def dehydrate_environment(self, ci_relation):
        return ci_relation.child.id

    def get_queryset(self):
        return models_ci.CIRelation.objects.filter(
            type=models_ci.CI_RELATION_TYPES.CONTAINS,
            parent__in=models_device.ServiceCatalog.objects.all(),
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
    name = fields.Field(column_name='name')
    profit_center = fields.Field(column_name='profit_center')

    def dehydrate_name(self, service):
        return service.name

    def dehydrate_profit_center(self, service):
        profit_center = service.child.filter(
            parent__type=models_ci.CI_TYPES.PROFIT_CENTER,
        )
        assert len(profit_center) < 2, 'found many profit centers'
        if profit_center:
            profit_center_name = profit_center[0].parent.name
        else:
            profit_center_name = ''
        return profit_center_name

    def get_queryset(self):
        return models_device.ServiceCatalog.objects.all()

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


class RackResource(resources.ModelResource):
    class Meta:
        exclude = ('data_center', 'accessories', 'deprecated_ralph_rack',)
        model = models_dc_assets.Rack


class SupportTypeResource(resources.ModelResource):

    class Meta:
        fields = ['id', 'name']
        model = models_support.SupportType


class SupportResource(resources.ModelResource):
    remarks = fields.Field(column_name='additional_notes')
    base_objects = fields.Field()

    class Meta:
        fields = [
            'contract_id', 'description', 'price', 'date_from', 'date_to',
            'escalation_path', 'contract_terms', 'remarks',
            'sla_type', 'asset_type', 'status', 'producer', 'supplier',
            'serial_no', 'invoice_no', 'invoice_date', 'period_in_months',
            'support_type', 'base_objects', 'name', 'region',
        ]
        model = models_support.Support

    def dehydrate_base_objects(self, support):
        return ",".join(map(
            unicode,
            support.assets.all().values_list('id', flat=True)
        ))


class EnvironmentResource(resources.ModelResource):
    class Meta:
        fields = ('id', 'name', 'created', 'modified',)
        model = models_device.DeviceEnvironment


class GenericComponentResource(resources.ModelResource):
    asset = fields.Field()

    def dehydrate_model(self, component):
        try:
            model_name = component.model.name or ''
        except AttributeError:
            model_name = ''
        return model_name

    def dehydrate_asset(self, component):
        try:
            sn = component.device.get_asset().sn or ''
        except AttributeError:
            sn = ''
        return sn

    class Meta:
        model = models_component.GenericComponent


class LicenceResource(resources.ModelResource):
    class Meta:
        model = Licence
        fields = [
            'id', 'created', 'modified', 'manufacturer',
            'number_bought', 'sn', 'niw', 'valid_thru',
            'order_no', 'price', 'accounting_id', 'invoice_date', 'provider',
            'invoice_no', 'remarks', 'license_details', 'licence_type',
            'software_category', 'region',
        ]


class BaseObjectLicenceResource(resources.ModelResource):

    base_object = fields.Field()

    class Meta:
        model = LicenceAsset
        fields = ['licence', 'base_object', 'quantity']

    def get_queryset(self):
        return LicenceAsset.objects.filter(
            asset__in=models_assets.Asset.objects.all(),
            licence__in=Licence.objects.all(),
        )

    def dehydrate_base_object(self, licence_asset):
        asset_type = models_assets.AssetType.from_id(
            licence_asset.asset.type
        ).group.name
        return "{}|{}".format(
            asset_type,
            licence_asset.asset.pk
        )


class RegionResource(resources.ModelResource):
    users = fields.Field()

    class Meta:
        model = Region
        fields = ['id', 'name', 'users']

    def dehydrate_users(self, region):
        return ','.join([u.username for u in region.profile.all()])
