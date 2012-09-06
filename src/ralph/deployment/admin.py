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

from ralph.deployment.models import Deployment, Preboot, PrebootFile


class DeploymentAdminForm(forms.ModelForm):
    class Meta:
        model = Deployment

    def clean(self):
        cleaned_data = super(DeploymentAdminForm, self).clean()
        ip = self.cleaned_data.get('ip')
        venture_role = self.cleaned_data.get('venture_role')
        if venture_role.check_ip(ip) is False:
            msg = _("Given IP isn't in the appropriate subnet")
            self._errors["ip"] = self.error_class([msg])
        return cleaned_data

class DeploymentAdmin(ModelAdmin):
    list_display = ('device', 'mac', 'status', 'venture', 'venture_role')
    list_filter = ('status', 'status_lastchanged')
    search_fields = ('device__name', 'mac', 'venture__name', 'venture__symbol',
        'venture_role__name', 'venture_role__symbol', 'issue_key')
    save_on_top = True
    related_search_fields = {
        'device': ['^name', '^model__name', '^ipaddress__hostname'],
        'venture': ['^name'],
        'venture_role': ['^name'],
    }
    form = DeploymentAdminForm

admin.site.register(Deployment, DeploymentAdmin)


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

    list_display = ('name', 'ftype', config_slug)
    list_filter = ('ftype',)
    search_fields = ('name', 'raw_config')
    save_on_top = True

admin.site.register(PrebootFile, PrebootFileAdmin)
