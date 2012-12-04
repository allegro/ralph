#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ajax_select import LookupChannel
from django.utils.html import escape
from django.db.models import Q

from ralph.assets.models_assets import (
    Asset,
    AssetManufacturer,
    AssetModel,
    AssetSource,
    AssetStatus,
    AssetType,
    DeviceInfo,
    LicenseType,
    OfficeInfo,
    PartInfo,
    Warehouse,
)
from ralph.assets.models_history import AssetHistoryChange


class DeviceLookup(LookupChannel):
    model = Asset

    def get_query(self, q, request):
        query = Q(
            Q(device_info__gt=0) & Q(
                Q(barcode__istartswith=q) |
                Q(sn__istartswith=q) |
                Q(model__name__icontains=q)
            )
        )
        return self.get_base_objects().filter(query).order_by('sn')[:10]

    def get_result(self, obj):
        return obj.id

    def format_match(self, obj):
        return self.format_item_display(obj)

    def format_item_display(self, obj):
        return """
        <li class='das-container'>
            <span class='das-model'>%s</span>
            <span class='das-barcode'>%s</span>
            <span class='das-sn'>%s</span>
        </li>
        """ % (escape(obj.model), escape(obj.barcode or ''), escape(obj.sn))


class AssetModelLookup(LookupChannel):
    model = AssetModel

    def get_query(self, q, request):
        return AssetModel.objects.filter(
            Q(name__icontains=q)
        ).order_by('name')[:10]

    def get_result(self, obj):
        return obj.id

    def format_match(self, obj):
        return self.format_item_display(obj)

    def format_item_display(self, obj):
        return "%s %s" % (escape(obj.name), escape(obj.manufacturer))


class WarehouseLookup(LookupChannel):
    model = Warehouse

    def get_query(self, q, request):
        return Warehouse.objects.filter(
            Q(name__icontains=q)
        ).order_by('name')[:10]

    def get_result(self, obj):
        return obj.id

    def format_match(self, obj):
        return self.format_item_display(obj)

    def format_item_display(self, obj):
        return escape(obj.name)


class DCDeviceLookup(DeviceLookup):
    def get_base_objects(self):
        return Asset.objects_dc()


class BODeviceLookup(DeviceLookup):
    def get_base_objects(self):
        return Asset.objects_bo()


__all__ = [
    'Asset',
    'AssetManufacturer',
    'AssetModel',
    'AssetSource',
    'AssetStatus',
    'AssetType',
    'DeviceInfo',
    'LicenseType',
    'OfficeInfo',
    'PartInfo',
    'Warehouse',
    'DeviceLookup',
    'DCDeviceLookup',
    'BODeviceLookup',
    'AssetModelLookup',
    'AssetHistoryChange',
]
