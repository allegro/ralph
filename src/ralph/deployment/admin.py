#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib import admin
from lck.django.common.admin import ModelAdmin

from ralph.deployment.models import Deployment, Preboot, PrebootFile


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

admin.site.register(Deployment, DeploymentAdmin)


class PrebootAdmin(ModelAdmin):
    def config_slug(self):
        return self.raw_config.replace('\r', '').replace('\n', ' ')[:40]
    config_slug.short_description = _("config")

    list_display = ('name', config_slug)
    filter_horizontal = ('files',)
    search_fields = ('name', 'raw_config')
    save_on_top = True

admin.site.register(Preboot, PrebootAdmin)


class PrebootFileAdmin(ModelAdmin):
    def file_with_size(self):
        template = """{filename} - {size:.2f} MB"""
        return template.format(
            filename=self.name,
            size=self.file.size/1024/1024,
        )
    file_with_size.short_description = _("name")
    list_display = (file_with_size)
    list_filter = ('ftype',)
    search_fields = ('name',)
    save_on_top = True

admin.site.register(PrebootFile, PrebootFileAdmin)
