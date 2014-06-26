#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re
import logging

from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from lck.django.common.admin import (
    ForeignKeyAutocompleteTabularInline,
    ModelAdmin,
)
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.template.defaultfilters import slugify

from ralph.discovery import models as m
from ralph.business.admin import RolePropertyValueInline
from ralph.ui.forms.network import NetworkForm


SAVE_PRIORITY = 215
HOSTS_NAMING_TEMPLATE_REGEX = re.compile(r'<[0-9]+,[0-9]+>.*\.[a-zA-Z0-9]+')


def copy_network(modeladmin, request, queryset):
    for net in queryset:
        name = 'Copy of %s' % net.name
        address = net.address.rsplit('/', 1)[0] + '/1'
        new_net = m.Network(
            name=name,
            address=address,
            gateway=net.gateway,
            kind=net.kind,
            data_center=net.data_center,
        )
        try:
            new_net.save()
        except ValidationError:
            messages.error(request, "Network %s already exists." % address)
        except Exception:
            message = "Failed to create %s." % address
            messages.error(request, message)
            logging.exception(message)
        else:
            new_net.terminators = net.terminators.all()
            new_net.save()

copy_network.short_description = "Copy network"


class NetworkAdmin(ModelAdmin):

    def address(self):
        return self.address

    address.short_description = _("network address")
    address.admin_order_field = 'min_ip'

    def gateway(self):
        return self.gateway

    gateway.short_description = _("gateway address")
    gateway.admin_order_field = 'gateway_as_int'

    def terms(self):
        return ", ".join([n.name for n in self.terminators.order_by('name')])

    terms.short_description = _("network terminators")

    list_display = ('name', 'vlan', address, gateway, terms, 'data_center',
                    'environment', 'kind')

    list_filter = (
        'data_center', 'terminators', 'environment', 'kind', 'dhcp_broadcast',
    )
    list_per_page = 250
    radio_fields = {
        'data_center': admin.HORIZONTAL,
        'environment': admin.HORIZONTAL,
        'kind': admin.HORIZONTAL,
    }
    search_fields = ('name', 'address', 'vlan')
    filter_horizontal = ('terminators', 'racks', 'custom_dns_servers')
    save_on_top = True
    form = NetworkForm
    actions = [copy_network]

admin.site.register(m.Network, NetworkAdmin)


class NetworkKindAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

admin.site.register(m.NetworkKind, NetworkKindAdmin)


class NetworkTerminatorAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

admin.site.register(m.NetworkTerminator, NetworkTerminatorAdmin)


class DataCenterAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

admin.site.register(m.DataCenter, DataCenterAdmin)


class EnvironmentAdminForm(forms.ModelForm):

    class Meta:
        model = m.Environment

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if slugify(name) != name.lower():
            raise forms.ValidationError(
                _('You can use only this characters: [a-zA-Z0-9_-]')
            )
        return name

    def clean_hosts_naming_template(self):
        template = self.cleaned_data['hosts_naming_template']
        if re.search("[^a-z0-9<>,\.|-]", template):
            raise forms.ValidationError(
                _("Please remove disallowed characters."),
            )
        for part in template.split("|"):
            if not HOSTS_NAMING_TEMPLATE_REGEX.search(part):
                raise forms.ValidationError(
                    _(
                        "Incorrect template structure. Please see example "
                        "below.",
                    ),
                )
        return template


class EnvironmentAdmin(ModelAdmin):
    list_display = (
        'name',
        'data_center',
        'queue',
        'domain',
        'hosts_naming_template',
        'next_server'
    )
    search_fields = ('name',)
    form = EnvironmentAdminForm
    list_filter = ('data_center', 'queue')

admin.site.register(m.Environment, EnvironmentAdmin)


class DiscoveryQueueAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

admin.site.register(m.DiscoveryQueue, DiscoveryQueueAdmin)


class IPAddressForm(forms.ModelForm):

    class Meta:
        model = m.IPAddress

    def clean(self):
        address = self.cleaned_data.get('address')
        hostname = self.cleaned_data.get('hostname')
        if not address and hostname:
            raise forms.ValidationError(_("Either address or hostname must "
                                          "be provided."))


class IPAddressInline(ForeignKeyAutocompleteTabularInline):
    model = m.IPAddress
    readonly_fields = ('snmp_name', 'last_seen')
    exclude = ('created', 'modified', 'dns_info', 'http_family',
               'snmp_community', 'last_puppet')
    edit_separately = True
    extra = 0
    related_search_fields = {
        'device': ['^name'],
        'network': ['^name'],
    }


class ChildDeviceInline(ForeignKeyAutocompleteTabularInline):
    model = m.Device
    edit_separately = True
    readonly_fields = ('name', 'model', 'sn', 'remarks', 'last_seen',)
    exclude = ('name2', 'created', 'modified', 'boot_firmware', 'barcode',
               'hard_firmware', 'diag_firmware', 'mgmt_firmware', 'price',
               'purchase_date', 'warranty_expiration_date', 'role',
               'support_expiration_date', 'deprecation_kind', 'margin_kind',
               'chassis_position', 'position', 'support_kind', 'management',
               'logical_parent')
    extra = 0
    related_search_fields = {
        'model': ['^name'],
    }
    fk_name = 'parent'


class DeviceModelAdmin(ModelAdmin):

    def count(self):
        return m.Device.objects.filter(model=self).count()

    list_display = ('name', 'type', count, 'created', 'modified')
    list_filter = ('type', 'group')
    search_fields = ('name',)

admin.site.register(m.DeviceModel, DeviceModelAdmin)


class DeviceModelInline(admin.TabularInline):
    model = m.DeviceModel
    exclude = ('created', 'modified')
    extra = 0


class DeviceModelGroupAdmin(ModelAdmin):

    def count(self):
        return m.Device.objects.filter(model__group=self).count()

    list_display = ('name', count, 'price')
    inlines = (DeviceModelInline,)

admin.site.register(m.DeviceModelGroup, DeviceModelGroupAdmin)


class DeviceForm(forms.ModelForm):

    class Meta:
        model = m.Device

    def clean_sn(self):
        sn = self.cleaned_data['sn']
        if not sn:
            sn = None
        return sn

    def clean_model(self):
        model = self.cleaned_data['model']
        if not model:
            raise forms.ValidationError(_("Model is required"))
        return model

    def clean_barcode(self):
        barcode = self.cleaned_data['barcode']
        return barcode or None


class ProcessorInline(ForeignKeyAutocompleteTabularInline):
    model = m.Processor
    # readonly_fields = ('label', 'index', 'speed')
    exclude = ('created', 'modified')
    extra = 0
    related_search_fields = {
        'model': ['^name'],
    }


class MemoryInline(ForeignKeyAutocompleteTabularInline):
    model = m.Memory
    exclude = ('created', 'modified')
    extra = 0
    related_search_fields = {
        'model': ['^name'],
    }


class EthernetInline(ForeignKeyAutocompleteTabularInline):
    model = m.Ethernet
    exclude = ('created', 'modified')
    extra = 0
    related_search_fields = {
        'model': ['^name'],
    }


class StorageInline(ForeignKeyAutocompleteTabularInline):
    model = m.Storage
    readonly_fields = (
        'label',
        'size',
        'sn',
        'model',
        'created',
        'modified',
        'mount_point',
    )
    extra = 0
    related_search_fields = {
        'model': ['^name'],
    }


class DeviceAdmin(ModelAdmin):
    form = DeviceForm
    inlines = [
        ProcessorInline,
        MemoryInline,
        EthernetInline,
        StorageInline,
        IPAddressInline,
        ChildDeviceInline,
        RolePropertyValueInline,
    ]
    list_display = ('name', 'sn', 'created', 'modified')
    list_filter = ('model__type',)
    list_per_page = 250
    readonly_fields = ('last_seen',)
    save_on_top = True
    search_fields = ('name', 'name2', 'sn', 'model__type',
                     'model__name', 'ethernet__mac')
    related_search_fields = {
        'parent': ['^name'],
        'logical_parent': ['^name'],
        'venture': ['^name'],
        'venture_role': ['^name'],
        'management': ['^address', '^hostname'],
        'model': ['^name', ],
    }

    def save_model(self, request, obj, form, change):
        obj.save(user=request.user, priority=SAVE_PRIORITY)

    def save_formset(self, request, form, formset, change):
        if formset.model.__name__ == 'RolePropertyValue':
            for instance in formset.save(commit=False):
                instance.save(user=request.user)
        else:
            formset.save(commit=True)

admin.site.register(m.Device, DeviceAdmin)


class IPAliasInline(admin.TabularInline):
    model = m.IPAlias
    exclude = ('created', 'modified')
    extra = 0


class IPAddressAdmin(ModelAdmin):
    inlines = [IPAliasInline]

    def ip_address(self):
        """Used for proper ordering."""
        return self.address
    ip_address.short_description = _("IP address")
    ip_address.admin_order_field = 'number'

    list_display = (
        ip_address, 'hostname', 'device', 'snmp_name', 'is_public', 'created',
        'modified',
    )
    list_filter = ('is_public', 'snmp_community')
    list_per_page = 250
    save_on_top = True
    search_fields = ('address', 'hostname', 'number', 'snmp_name')
    related_search_fields = {
        'device': ['^name'],
        'network': ['^name'],
        'venture': ['^name'],
    }

admin.site.register(m.IPAddress, IPAddressAdmin)


class DeprecationKindAdmin(ModelAdmin):
    save_on_top = True
    list_display = ('name', 'months', 'default')
admin.site.register(m.DeprecationKind, DeprecationKindAdmin)


class MarginKindAdmin(ModelAdmin):
    save_on_top = True
admin.site.register(m.MarginKind, MarginKindAdmin)


class LoadBalancerVirtualServerAdmin(ModelAdmin):
    pass

admin.site.register(
    m.LoadBalancerVirtualServer,
    LoadBalancerVirtualServerAdmin,
)


class LoadBalancerMemberAdmin(ModelAdmin):
    pass

admin.site.register(
    m.LoadBalancerMember,
    LoadBalancerMemberAdmin,
)


class ComponentModelInline(admin.TabularInline):
    model = m.ComponentModel
    exclude = ('created', 'modified')
    extra = 0


class ComponentModelAdmin(ModelAdmin):

    def count(self):
        return self.get_count()

    list_filter = ('type', 'group')
    list_display = ('name', 'type', count, 'family', 'group')
    search_fields = ('name', 'type', 'group__name', 'family')

admin.site.register(m.ComponentModel, ComponentModelAdmin)


class GenericComponentAdmin(ModelAdmin):
    search_fields = ('label', 'sn', 'model__name')
    list_display = ('label', 'model', 'sn')
    related_search_fields = {
        'device': ['^name'],
        'model': ['^name']
    }

admin.site.register(m.GenericComponent, GenericComponentAdmin)


class ComponentModelGroupAdmin(ModelAdmin):

    def count(self):
        return sum([
            m.Memory.objects.filter(model__group=self).count(),
            m.Processor.objects.filter(model__group=self).count(),
            m.Storage.objects.filter(model__group=self).count(),
            m.FibreChannel.objects.filter(model__group=self).count(),
            m.DiskShare.objects.filter(model__group=self).count(),
            m.Software.objects.filter(model__group=self).count(),
            m.OperatingSystem.objects.filter(model__group=self).count(),
            m.GenericComponent.objects.filter(model__group=self).count(),
        ])
    inlines = [ComponentModelInline]
    list_display = ('name', count, 'price')

admin.site.register(m.ComponentModelGroup, ComponentModelGroupAdmin)


class DiskShareMountInline(ForeignKeyAutocompleteTabularInline):
    model = m.DiskShareMount
    exclude = ('created', 'modified')
    related_search_fields = {
        'device': ['^name'],
        'server': ['^name'],
        'address': ['^address'],
    }
    extra = 0


class DiskShareAdmin(ModelAdmin):
    inlines = [DiskShareMountInline]
    search_fields = ('wwn',)
    related_search_fields = {
        'device': ['^name'],
        'model': ['^name']
    }

admin.site.register(m.DiskShare, DiskShareAdmin)


class HistoryChangeAdmin(ModelAdmin):
    list_display = ('date', 'user', 'device', 'component', 'field_name',
                    'old_value', 'new_value')
    list_per_page = 250
    readonly_fields = ('date', 'device', 'user', 'field_name', 'new_value',
                       'old_value', 'component')
    search_fields = ('user__username', 'field_name', 'new_value')

admin.site.register(m.HistoryChange, HistoryChangeAdmin)


class DiscoveryWarningAdmin(ModelAdmin):
    list_display = ('message', 'count', 'date', 'plugin', 'ip', 'device')
    list_per_page = 250
    readonly_fields = ('date', 'plugin', 'message', 'ip', 'count', 'device')
    search_fields = ('plugin', 'ip', 'message')

admin.site.register(m.DiscoveryWarning, DiscoveryWarningAdmin)
