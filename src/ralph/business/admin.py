#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from lck.django.common.admin import ModelAdmin, ForeignKeyAutocompleteTabularInline

from ralph.business.models import Venture, VentureRole, OwnerType, VentureOwner
from ralph.business.models import VentureExtraCost
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
    model = VentureOwner
    exclude = ('created', 'modified')
    extra = 4


class VentureRoleInline(ForeignKeyAutocompleteTabularInline):
    model = VentureRole
    exclude = ('created', 'modified')
    extra = 4
    related_search_fields = {
        'parent': ['^parent'],
    }

class VentureExtraCostInline(admin.TabularInline):
    model = VentureExtraCost
    exclude = ('created', 'modified')


class VentureRoleAdmin(ModelAdmin):
    inlines = [RolePropertyInline, RoleIntegrationInline]
    related_search_fields = {
        'venture': ['^name'],
        'parent': ['^parent'],
    }

admin.site.register(VentureRole, VentureRoleAdmin)


class RolePropertyValueInline(admin.TabularInline):
    model = RolePropertyValue
    extra = 0

class SubVentureInline(admin.TabularInline):
    model = Venture
    exclude = ('created', 'modified',)
    extra = 0


class VentureAdmin(ModelAdmin):
    inlines = [
                VentureExtraCostInline,
                VentureOwnerInline,
                VentureRoleInline,
                SubVentureInline,
              ]
    related_search_fields = {
        'parent': ['^parent'],
    }

    def members(self):
        from ralph.discovery.models import Device
        return str(Device.objects.filter(venture=self).count())
    members.short_description = _("members")

    def technical_owners(self):
        owners = VentureOwner.objects.filter(type=OwnerType.technical.id,
            venture=self)
        return ", ".join([owner.link_if_possible() for owner in owners])
    technical_owners.short_description = _("technical owners")
    technical_owners.allow_tags = True

    def business_owners(self):
        owners = VentureOwner.objects.filter(type=OwnerType.business.id,
            venture=self)
        return ", ".join([owner.link_if_possible() for owner in owners])
    business_owners.short_description = _("business owners")
    business_owners.allow_tags = True

    list_display = ('name', 'path', 'data_center', members, technical_owners, business_owners)
    list_filter = ('data_center', 'show_in_ralph', 'parent')
    search_fields = ('name', 'ventureowner__name')
    save_on_top = True

admin.site.register(Venture, VentureAdmin)


class DepartmentAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    save_on_top = True

admin.site.register(Department, DepartmentAdmin)
