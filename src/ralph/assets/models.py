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
    model = Asset

    def get_query(self, q, request):
        query = Q(
            Q(device_info__gt=0) & Q(
                Q(barcode__istartswith=q) |
                Q(sn__istartswith=q) |
                Q(model__name__istartswith=q)
            )
        )
        return Asset.objects_dc().filter(query).order_by('sn')[:10]

    def get_result(self, obj):
        return obj.id

    def format_match(self, obj):
        return self.format_item_display(obj)

    def format_item_display(self, obj):
        return """
        <div style='border-bottom: solid #ddd 1px'>
            <div>model: <b>%s</b></div>
            <div>bc:<b>%s</b></div>
            <div>sn:<b>%s</b></div>
        </div>
        """ % (escape(obj.model), escape(obj.barcode), escape(obj.sn))


class AssetModelLookup(LookupChannel):
    model = AssetModel

    def get_query(self, q, request):
        return AssetModel.objects.filter(Q(name__istartswith=q)).order_by('name')[:10]

    def get_result(self, obj):
        return obj.id

    def format_match(self, obj):
        return self.format_item_display(obj)

    def format_item_display(self, obj):
        return "%s %s" % (escape(obj.name), escape(obj.manufacturer))

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