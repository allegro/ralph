#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from lck.django.common.admin import ModelAdmin, ForeignKeyAutocompleteTabularInline

from ralph.business.models import (Venture, VentureRole,
    VentureExtraCost, VentureExtraCostType)
from ralph.cmdb.models_ci import CIOwner, CI, CIOwnershipType
from ralph.business.models import (RoleProperty, RolePropertyType,
        RolePropertyTypeValue, RolePropertyValue, Department)
from ralph.integration.admin import RoleIntegrationInline


class RolePropertyTypeValueInline(admin.TabularInline):
    model = RolePropertyTypeValue


class RolePropertyTypeAdmin(ModelAdmin):
    inlines = [RolePropertyTypeValueInline]

admin.site.register(RolePropertyType, RolePropertyTypeAdmin)


class RolePropertyInline(admin.TabularInline):
    model = RoleProperty


class VentureOwnerInline(admin.TabularInline):
    model = CIOwner
    exclude = ('created', 'modified')
    extra = 4


class VentureRoleInline(ForeignKeyAutocompleteTabularInline):
    model = VentureRole
    exclude = ('created', 'modified')
    extra = 4
    related_search_fields = {
        'parent': ['^name'],
    }


class VentureExtraCostInline(admin.TabularInline):
    model = VentureExtraCost
    exclude = ('created', 'modified')


class AutocompleteVentureExtraCostInline(ForeignKeyAutocompleteTabularInline):
    model = VentureExtraCost
    exclude = ('created', 'modified')
    extra = 3
    related_search_fields = {
        'venture': ['^name'],
    }


class VentureRoleAdmin(ModelAdmin):
    inlines = [RolePropertyInline, RoleIntegrationInline]
    related_search_fields = {
        'venture': ['^name'],
        'parent': ['^name'],
    }
    filter_horizontal = ('networks',)

admin.site.register(VentureRole, VentureRoleAdmin)


class VentureExtraCostTypeAdmin(ModelAdmin):
    inlines = [AutocompleteVentureExtraCostInline, ]

admin.site.register(VentureExtraCostType, VentureExtraCostTypeAdmin)


class RolePropertyValueInline(admin.TabularInline):
    model = RolePropertyValue
    extra = 0


class SubVentureInline(admin.TabularInline):
    model = Venture
    exclude = ('created', 'modified',)
    extra = 0


class VentureAdminForm(forms.ModelForm):
    def clean_symbol(self):
        data = self.cleaned_data['symbol']
        if not data:
            raise forms.ValidationError(_("symbol must be given"))
        return data


class VentureAdmin(ModelAdmin):
    inlines = [
                VentureExtraCostInline,
                VentureOwnerInline,
                VentureRoleInline,
                SubVentureInline,
              ]
    related_search_fields = {
        'parent': ['^name'],
    }
    form = VentureAdminForm

    def members(self):
        from ralph.discovery.models import Device
        return str(Device.objects.filter(venture=self).count())
    members.short_description = _("members")

    def technical_owners(self):
        ci = CI.get_by_content_object(self)
        if not ci:
            return []
        owners = CIOwner.objects.filter(ciownership__type=CIOwnershipType.technical.id,
            ci=ci)
        return ", ".join([unicode(owner) for owner in owners])
    technical_owners.short_description = _("technical owners")
    technical_owners.allow_tags = True

    def business_owners(self):
        ci = CI.get_by_content_object(self)
        if not ci:
            return []
        owners = CIOwner.objects.filter(ciownership__type=CIOwnershipType.business.id,
            ci=ci)
        return ", ".join([unicode(owner) for owner in owners])
    business_owners.short_description = _("business owners")
    business_owners.allow_tags = True

    list_display = ('name', 'path', 'data_center', members, technical_owners, business_owners)
    list_filter = ('data_center', 'show_in_ralph', 'parent')
    filter_horizontal = ('networks',)
    search_fields = ('name', 'ventureowner__name')
    save_on_top = True

admin.site.register(Venture, VentureAdmin)


class DepartmentAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    save_on_top = True

admin.site.register(Department, DepartmentAdmin)
