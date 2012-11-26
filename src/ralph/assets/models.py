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
    LicenseTypes,
    OfficeInfo,
    PartInfo,
    Warehouse,
)


class DeviceLookup(LookupChannel):
    model = DeviceInfo

    def get_query(self, q, request):
        query = Q(
            Q(barcode__istartswith=q) |
            Q(sn__istartswith=q)
        )
        return DeviceInfo.objects.filter(Q).order_by('name')[:10]

    def get_result(self, obj):
        return obj.name

    def format_match(self, obj):
        return self.format_item_display(obj)

    def format_item_display(self, obj):
        return "%s<div><i>%s</i></div>" % (escape(obj.model), escape(obj.barcode))


class AssetModelLookup(LookupChannel):
    model = AssetModel

    def get_query(self, q, request):
        return AssetModel.objects.filter(Q(name__istartswith=q)).order_by('name')[:10]

    def get_result(self, obj):
        return obj.name

    def format_match(self, obj):
        return self.format_item_display(obj)

    def format_item_display(self, obj):
        return "%s<div><i>%s</i></div>" % (escape(obj.name), escape(obj.id))

__all__ = [
    Asset,
    AssetManufacturer,
    AssetModel,
    AssetSource,
    AssetStatus,
    AssetType,
    DeviceInfo,
    LicenseTypes,
    OfficeInfo,
    PartInfo,
    Warehouse,
    DeviceLookup,
    AssetModelLookup,
]