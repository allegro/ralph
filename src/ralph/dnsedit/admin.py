# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from lck.django.common.admin import ModelAdmin

from ralph.dnsedit.models import DHCPEntry, DNSHistory, DHCPServer, DNSServer


class DHCPEntryAdminForm(forms.ModelForm):

    class Meta:
        model = DHCPEntry

    def clean_ip(self):
        ip = self.cleaned_data['ip']
        queryset = DHCPEntry.objects.filter(ip=ip)
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)
        if queryset.count() > 0:
            raise forms.ValidationError(
                _('DHCP entry with this IP address already exists.'),
            )
        return ip


class DHCPEntryAdmin(ModelAdmin):

    def ip_address(self):
        return self.ip
    ip_address.short_description = _("IP address")
    ip_address.admin_order_field = 'number'

    list_display = (ip_address, 'mac')
    search_fields = ('ip', 'mac')
    save_on_top = True
    form = DHCPEntryAdminForm

admin.site.register(DHCPEntry, DHCPEntryAdmin)


class DHCPServerAdmin(ModelAdmin):
    list_display = ('ip', 'last_synchronized')
    search_fields = ('ip',)
    save_on_top = True

admin.site.register(DHCPServer, DHCPServerAdmin)


class DNSHistoryAdmin(ModelAdmin):
    list_display = ('record_name', 'record_type', 'date', 'user', 'field_name',
                    'old_value', 'new_value')
    search_fields = ('record_name', 'old_value', 'new_value', 'field_name',
                     'date')
    list_filter = ('record_type', 'date', 'field_name')
    save_on_top = True

admin.site.register(DNSHistory, DNSHistoryAdmin)


class DNSServerAdmin(ModelAdmin):
    list_display = ('ip_address', 'is_default')
    search_fields = ('ip_address',)
    list_filter = ('is_default',)
    save_on_top = True

admin.site.register(DNSServer, DNSServerAdmin)
