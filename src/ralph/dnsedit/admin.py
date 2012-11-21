# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib import admin

from lck.django.common.admin import ModelAdmin

from ralph.dnsedit.models import DHCPEntry, DNSHistory


class DHCPEntryAdmin(ModelAdmin):
    list_display = ('ip', 'mac')
    search_fields = ('ip', 'mac')
    save_on_top = True

admin.site.register(DHCPEntry, DHCPEntryAdmin)


class DNSHistoryAdmin(ModelAdmin):
    list_display = ('record_name', 'record_type', 'date', 'user', 'field_name',
                    'old_value', 'new_value')
    search_fields = ('record_name', 'old_value', 'new_value', 'field_name',
                     'date')
    list_filter = ('record_type', 'date', 'field_name')
    save_on_top = True

admin.site.register(DNSHistory, DNSHistoryAdmin)
