#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib import admin
from lck.django.common.admin import ModelAdmin

from ralph.deployment.models import Deployment


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
