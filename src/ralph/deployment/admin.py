#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from lck.django.common.admin import ModelAdmin

from ralph.deployment.models import (
    ArchivedDeployment, Deployment, Preboot, PrebootFile, MassDeployment,
)
from ralph.deployment.util import clean_hostname


class MassDeploymentAdmin(ModelAdmin):
    list_display = (
        'created', 'modified', 'created_by', 'modified_by', 'is_done',
    )
    search_fields = (
        'created_by__user__username', 'created_by__user__first_name',
        'created_by__user__last_name',
    )

admin.site.register(
    MassDeployment, MassDeploymentAdmin
)


class DeploymentAdminForm(forms.ModelForm):

    class Meta:
        model = Deployment

    def clean_hostname(self):
        hostname = self.cleaned_data.get('hostname')
        return clean_hostname(hostname)


class DeploymentAdmin(ModelAdmin):
    list_display = (
        'device', 'mac', 'status', 'venture', 'venture_role',
        'mass_deployment', 'user', 'created',
    )
    list_filter = ('status', 'status_lastchanged',)
    search_fields = (
        'device__name', 'mac', 'venture__name', 'venture__symbol',
        'venture_role__name', 'user__last_name',
    )
    save_on_top = True
    related_search_fields = {
        'device': ['^name', '^model__name', '^ipaddress__hostname'],
        'venture': ['^name'], 'venture_role': ['^name'],
    }
    form = DeploymentAdminForm

    def _move_deployment_to_archive(modeladmin, request, queryset):
        for deployment in queryset:
            deployment.archive()

    _move_deployment_to_archive.short_description = _('Move to archive')

    actions = [_move_deployment_to_archive, ]


admin.site.register(Deployment, DeploymentAdmin)


class ArchivedDeploymentAdmin(DeploymentAdmin):
    readonly_fields = tuple(ArchivedDeployment._meta.get_all_field_names())

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(ArchivedDeployment, ArchivedDeploymentAdmin)


class PrebootAdmin(ModelAdmin):

    def file_list(self):
        result = ", ".join([f.name for f in self.files.all()])
        return result
    file_list.short_description = _("files")

    list_display = ('name', file_list)
    filter_horizontal = ('files',)
    search_fields = ('name',)
    save_on_top = True

admin.site.register(Preboot, PrebootAdmin)


class PrebootFileAdmin(ModelAdmin):

    def config_slug(self):
        if self.file:
            return self.get_filesize_display()
        slug = self.raw_config.replace('\r', '').replace('\n', ' ')
        if len(slug) > 50:
            slug = slug[:50] + " (...)"
        return slug
    config_slug.short_description = _("details")

    fieldsets = (
        (None, {'fields': ['name', 'ftype']}),
        (_("content").capitalize(), {
            'fields': ['file', 'raw_config'],
            'description': _("Fill either <b>file</b> or <b>raw config</b>."),
        }),
        (None, {'fields': ['description', ]}),
    )
    list_display = ('name', 'ftype', config_slug)
    list_filter = ('ftype',)
    radio_fields = {'ftype': admin.HORIZONTAL}
    search_fields = ('name', 'raw_config')
    save_on_top = True

admin.site.register(PrebootFile, PrebootFileAdmin)
