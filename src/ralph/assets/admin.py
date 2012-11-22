#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib import admin
from lck.django.common.admin import ModelAdmin

from ralph.assets.models import (
    Asset, AssetManufacturer, AssetModel, OfficeData, DeviceInfo, PartInfo,
    Magazine,
)


class MagazineAdmin(ModelAdmin):
    save_on_top = True
    list_display = ('name',)
    search_fields = ('name',)

admin.site.register(Magazine, MagazineAdmin)


class AssetModelAdmin(ModelAdmin):
    save_on_top = True
    list_display = ('name',)
    search_fields = ('name',)

admin.site.register(AssetModel, AssetModelAdmin)


class AssetManufacturerAdmin(ModelAdmin):
    save_on_top = True
    list_display = ('name',)
    search_fields = ('name',)

admin.site.register(AssetManufacturer, AssetManufacturerAdmin)


class AssetAdmin(ModelAdmin):
    save_on_top = True
    list_display = ('model', 'type', 'status', 'sn', 'barcode')

admin.site.register(Asset, AssetAdmin)


class DeviceInfoAdmin(ModelAdmin):
    def location(self):
        return self.location
    list_display = ('ralph_device', 'size', location)
    save_on_top = True

admin.site.register(DeviceInfo, DeviceInfoAdmin)


class PartInfoAdmin(ModelAdmin):
    list_display = ('device', 'source_device', 'barcode_salvaged',)
    save_on_top = True

admin.site.register(PartInfo, PartInfoAdmin)


class OfficeDataAdmin(ModelAdmin):
    list_display = ('license_key', 'license_type', 'date_of_last_inventory',)
    save_on_top = True

admin.site.register(OfficeData, OfficeDataAdmin)
