#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django import forms
from django.contrib import admin
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from lck.django.common.admin import ModelAdmin, ForeignKeyAutocompleteTabularInline

from ralph.business.models import (Venture, VentureRole,
    VentureExtraCost, VentureExtraCostType)
from ralph.cmdb.models_ci import CIOwner, CI, CIOwnershipType
from ralph.business.models import (RoleProperty, RolePropertyType,
        RolePropertyTypeValue, RolePropertyValue, Department)
from ralph.integration.admin import RoleIntegrationInline

import ralph.util.venture as util_venture


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
    exclude = ('created', 'modified', 'networks', 'preboot')
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


class VentureRoleAdminForm(forms.ModelForm):
    def clean_name(self):
        data = self.cleaned_data['name']
        if not util_venture.slug_validation(data):
            raise forms.ValidationError("Symbol can't be empty, has to start with"
                                        " a letter, and can't end with '_'. "
                                        "Allowed characters: a-z, 0-9, "
                                        "'_'. Example: simple_venture2")
        return data


class VentureRoleAdmin(ModelAdmin):
    def members(self):
        from ralph.discovery.models import Device
        return unicode(Device.objects.filter(venture=self).count())
    members.short_description = _("members")

    def venture_path(self):
        if not self.venture:
            return '---'
        else:
            return self.venture.path
    venture_path.short_description = _("venture_path")

    inlines = [RolePropertyInline, RoleIntegrationInline]
    related_search_fields = {
        'venture': ['^name'],
        'parent': ['^name'],
    }
    form = VentureRoleAdminForm
    filter_horizontal = ('networks',)
    list_display = ('name', venture_path, 'path', members)
    list_filter = ('venture__data_center', 'venture__show_in_ralph',)
    search_fields = ('name', 'venture__name', 'venture__path')
    save_on_top = True

admin.site.register(VentureRole, VentureRoleAdmin)


class VentureExtraCostTypeAdmin(ModelAdmin):
    inlines = [AutocompleteVentureExtraCostInline, ]

admin.site.register(VentureExtraCostType, VentureExtraCostTypeAdmin)


class RolePropertyValueInline(admin.TabularInline):
    model = RolePropertyValue
    extra = 0


class SubVentureInline(admin.TabularInline):
    model = Venture
    exclude = ('created', 'modified', 'networks', 'preboot',)
    extra = 0


class VentureAdminForm(forms.ModelForm):
    def clean_symbol(self):
        data = self.cleaned_data['symbol'].lower()
        if not util_venture.slug_validation(data):
            raise forms.ValidationError("Symbol can't be empty, has to start with"
                " a letter, and can't end with '_'. Allowed characters: a-z, 0-9, "
                "'_'. Example: simple_venture2")
        else:
            try:
                venture = Venture.objects.get(symbol=data)
                if venture != self.instance:
                    raise forms.ValidationError("Symbol already exist")
            except Venture.DoesNotExist:
                pass
        return data


class VentureAdmin(ModelAdmin):
    inlines = [
                VentureExtraCostInline,
                VentureRoleInline,
                SubVentureInline,
              ]
    related_search_fields = {
        'parent': ['^name'],
    }
    form = VentureAdminForm

    def members(self):
        from ralph.discovery.models import Device
        return unicode(Device.objects.filter(venture=self).count())
    members.short_description = _("members")

    def technical_owners(self):
        ci = CI.get_by_content_object(self)
        if not ci:
            return []
        owners = CIOwner.objects.filter(ciownership__type=CIOwnershipType.technical.id,
            ci=ci)
        part_url = reverse_lazy('ci_edit', kwargs={'ci_id': str(ci.id)})
        return "<a href=\"{}\">{}</a>".format(part_url,
                    ", ".join([unicode(owner) for owner in owners]))
    technical_owners.short_description = _("technical owners")
    technical_owners.allow_tags = True

    def business_owners(self):
        ci = CI.get_by_content_object(self)
        if not ci:
            return []
        owners = CIOwner.objects.filter(ciownership__type=CIOwnershipType.business.id,
            ci=ci)
        part_url = reverse_lazy('ci_edit', kwargs={'ci_id': str(ci.id)})
        return "<a href=\"{}\">{}</a>".format(part_url,
                    ", ".join([unicode(owner) for owner in owners]))
    business_owners.short_description = _("business owners")
    business_owners.allow_tags = True

    list_display = ('name', 'path', 'data_center', members, technical_owners, business_owners)
    list_filter = ('data_center', 'show_in_ralph',)
    filter_horizontal = ('networks',)
    search_fields = ('name', 'symbol')
    save_on_top = True

admin.site.register(Venture, VentureAdmin)


class DepartmentAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    save_on_top = True

admin.site.register(Department, DepartmentAdmin)
