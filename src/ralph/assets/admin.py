#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from lck.django.common.admin import ModelAdmin

from ralph.assets.models import (
    Asset,
    AssetCategory,
    AssetCategoryType,
    AssetManufacturer,
    AssetModel,
    OfficeInfo,
    DeviceInfo,
    PartInfo,
    Warehouse,
)


class WarehouseAdmin(ModelAdmin):
    save_on_top = True
    list_display = ('name',)
    search_fields = ('name',)

admin.site.register(Warehouse, WarehouseAdmin)


class AssetModelAdmin(ModelAdmin):
    save_on_top = True
    list_display = ('name',)
    search_fields = ('name',)

admin.site.register(AssetModel, AssetModelAdmin)


class AssetCategoryAdminForm(forms.ModelForm):
    def clean(self):
        data = self.cleaned_data
        parent = self.cleaned_data.get('parent')
        type = self.cleaned_data.get('type')
        if parent and parent.type != type:
            raise ValidationError(
                _("Parent type must be the same as selected type")
            )
        return data


class AssetCategoryAdmin(ModelAdmin):
    def name(self):
        type = AssetCategoryType.desc_from_id(self.type)
        if self.parent:
            name = '|-- ({}) {}'.format(type, self.name)
        else:
            name = '({}) {}'.format(type, self.name)
        return name
    form = AssetCategoryAdminForm
    save_on_top = True
    list_display = (name, 'parent')
    search_fields = ('name',)


admin.site.register(AssetCategory, AssetCategoryAdmin)


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


class OfficeInfoAdmin(ModelAdmin):
    list_display = ('license_key', 'license_type', 'date_of_last_inventory',)
    save_on_top = True

admin.site.register(OfficeInfo, OfficeInfoAdmin)
