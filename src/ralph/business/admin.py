#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from lck.django.common.admin import (ModelAdmin,
                                     ForeignKeyAutocompleteTabularInline)

from ralph.business.models import (
    BusinessSegment,
    Department,
    ProfitCenter,
    RoleProperty,
    RolePropertyType,
    RolePropertyTypeValue,
    RolePropertyValue,
    Venture,
    VentureRole,
)
from ralph.integration.admin import RoleIntegrationInline
from ralph.ui.widgets import ReadOnlyWidget
from ralph.util.di import is_extra_available, get_extra_data

import ralph.util.venture as util_venture


class RolePropertyTypeValueInline(admin.TabularInline):
    model = RolePropertyTypeValue


class RolePropertyTypeAdmin(ModelAdmin):
    inlines = [RolePropertyTypeValueInline]

admin.site.register(RolePropertyType, RolePropertyTypeAdmin)


class RolePropertyInline(admin.TabularInline):
    model = RoleProperty
    exclude = ('venture',)


class VenturePropertyInline(admin.TabularInline):
    model = RoleProperty
    exclude = ('role',)


class VentureRoleInline(ForeignKeyAutocompleteTabularInline):
    model = VentureRole
    exclude = ('created', 'modified', 'preboot')
    extra = 4
    related_search_fields = {
        'parent': ['^name'],
    }


class VentureRoleAdminForm(forms.ModelForm):

    def clean_name(self):
        data = self.cleaned_data['name']
        if not util_venture.slug_validation(data):
            raise forms.ValidationError(
                "Symbol can't be empty, has to start with"
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
    list_display = ('name', venture_path, 'path', members)
    list_filter = ('venture__data_center', 'venture__show_in_ralph',)
    search_fields = ('name', 'venture__name', 'venture__path')
    save_on_top = True

admin.site.register(VentureRole, VentureRoleAdmin)


class RolePropertyValueInline(admin.TabularInline):
    model = RolePropertyValue
    extra = 0


class SubVentureInline(admin.TabularInline):
    model = Venture
    exclude = ('created', 'modified', 'preboot',)
    extra = 0

    def __init__(self, *args, **kwargs):
        self.verbose_name = 'subventure'
        self.verbose_name_plural = 'subventures'
        super(SubVentureInline, self).__init__(*args, **kwargs)


class VentureAdminForm(forms.ModelForm):

    class Meta:
        model = Venture
        fields = [
            'name',
            'verified',
            'preboot',
            'data_center',
            'parent',
            'symbol',
            'show_in_ralph',
            'is_infrastructure',
            'margin_kind',
            'department',
            'business_segment',
            'profit_center',
        ]

    def clean_symbol(self):
        data = self.cleaned_data['symbol'].lower()
        if not util_venture.slug_validation(data):
            raise forms.ValidationError(
                "Symbol can't be empty, has to start with a letter, and can't "
                "end with '_'. Allowed characters: a-z, 0-9, '_'. "
                "Example: simple_venture2")
        else:
            try:
                venture = Venture.objects.get(symbol=data)
                if venture != self.instance:
                    raise forms.ValidationError("Symbol already exist")
            except Venture.DoesNotExist:
                pass
        return data

    def clean_business_segment(self):
        data = self.cleaned_data['business_segment']
        if not data:
            raise forms.ValidationError(
                "Business segment is required"
            )
        return data

    def clean_profit_center(self):
        data = self.cleaned_data['profit_center']
        if not data:
            raise forms.ValidationError(
                "Profit center segment is required"
            )
        return data


class VentureAdminVerifiedForm(VentureAdminForm):

    class Meta(VentureAdminForm.Meta):
        fields = [field for field in
                  VentureAdminForm.Meta.fields if field != 'verified']
        widgets = {
            'name': ReadOnlyWidget,
            'symbol': ReadOnlyWidget,
        }

        def clean_name(self):
            return self.instance.name

        def clean_symbol(self):
            return self.instance.symbol


class VentureAdmin(ModelAdmin):
    inlines = [
        SubVentureInline,
        VentureRoleInline,
        VenturePropertyInline,
    ]
    related_search_fields = {
        'parent': ['^name'],
    }

    def get_form(self, request, obj=None):
        if obj and obj.verified:
            return VentureAdminVerifiedForm
        return VentureAdminForm

    def has_delete_permission(self, request, obj=None):
        return False

    def members(self):
        from ralph.discovery.models import Device
        return unicode(Device.objects.filter(venture=self).count())
    members.short_description = _("members")
    list_display = [
        'name',
        'path',
        'data_center',
        members,
        'business_segment',
        'profit_center',
    ]
    if is_extra_available('ralph_obj_owner_column_factory'):
        list_display.insert(4, get_extra_data(
            'ralph_obj_owner_column_factory',
            'technical'
        ))
        list_display.insert(5, get_extra_data(
            'ralph_obj_owner_column_factory',
            'business'
        ))
    list_filter = ('data_center', 'show_in_ralph',)
    search_fields = (
        'name',
        'symbol',
        'business_segment__name',
        'profit_center__name',
    )
    save_on_top = True

admin.site.register(Venture, VentureAdmin)
admin.site.disable_action('delete_selected')


class DepartmentAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    save_on_top = True

admin.site.register(Department, DepartmentAdmin)


class ProfitCenterAdmin(ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')
    save_on_top = True

admin.site.register(ProfitCenter, ProfitCenterAdmin)


class BusinessSegmentAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    save_on_top = True

admin.site.register(BusinessSegment, BusinessSegmentAdmin)
