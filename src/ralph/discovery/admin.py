#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re
import logging

from django import forms
from django.conf import settings
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from lck.django.common.admin import (
    ForeignKeyAutocompleteTabularInline,
    ModelAdmin,
)
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.template.defaultfilters import slugify

from ralph.business.admin import RolePropertyValueInline
from ralph.discovery import models
from ralph.discovery import models_device
from ralph.ui.forms.network import NetworkForm
from ralph.ui.widgets import ReadOnlyWidget


SAVE_PRIORITY = 215
HOSTS_NAMING_TEMPLATE_REGEX = re.compile(r'<[0-9]+,[0-9]+>.*\.[a-zA-Z0-9]+')


def copy_network(modeladmin, request, queryset):
    for net in queryset:
        name = 'Copy of %s' % net.name
        address = net.address.rsplit('/', 1)[0] + '/1'
        new_net = models.Network(
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

admin.site.register(models.Network, NetworkAdmin)


class NetworkKindAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

admin.site.register(models.NetworkKind, NetworkKindAdmin)


class NetworkTerminatorAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

admin.site.register(models.NetworkTerminator, NetworkTerminatorAdmin)


class DataCenterAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

admin.site.register(models.DataCenter, DataCenterAdmin)


class EnvironmentAdminForm(forms.ModelForm):

    class Meta:
        model = models.Environment

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

admin.site.register(models.Environment, EnvironmentAdmin)


class DiscoveryQueueAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

admin.site.register(models.DiscoveryQueue, DiscoveryQueueAdmin)


class IPAddressInlineFormset(forms.models.BaseInlineFormSet):

    def get_queryset(self):
        qs = super(IPAddressInlineFormset, self).get_queryset().filter(
            is_management=False,
        )
        return qs


class IPAddressInline(ForeignKeyAutocompleteTabularInline):
    formset = IPAddressInlineFormset
    model = models.IPAddress
    readonly_fields = ('snmp_name', 'last_seen')
    exclude = ('created', 'modified', 'dns_info', 'http_family',
               'snmp_community', 'last_puppet', 'is_management')
    edit_separately = True
    extra = 0
    related_search_fields = {
        'device': ['^name'],
        'network': ['^name'],
    }


class ChildDeviceInline(ForeignKeyAutocompleteTabularInline):
    model = models.Device
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
        return models.Device.objects.filter(model=self).count()

    list_display = ('name', 'type', count, 'created', 'modified')
    list_filter = ('type',)
    search_fields = ('name',)

admin.site.register(models.DeviceModel, DeviceModelAdmin)


class DeviceModelInline(admin.TabularInline):
    model = models.DeviceModel
    exclude = ('created', 'modified')
    extra = 0


class DeviceForm(forms.ModelForm):

    class Meta:
        model = models.Device

    def __init__(self, *args, **kwargs):
        super(DeviceForm, self).__init__(*args, **kwargs)
        if self.instance.id is not None:
            asset = self.instance.get_asset()
            if asset:
                self.fields['dc'].widget = ReadOnlyWidget()
                self.fields['rack'].widget = ReadOnlyWidget()
                self.fields['chassis_position'].widget = ReadOnlyWidget()
                self.fields['position'].widget = ReadOnlyWidget()

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

    def clean(self):
        cleaned_data = super(DeviceForm, self).clean()
        model = self.cleaned_data.get('model')
        if all((
            'ralph_assets' in settings.INSTALLED_APPS,
            not self.instance.id,  # only when we create new device
            model
        )):
            if model and model.type not in models.ASSET_NOT_REQUIRED:
                raise forms.ValidationError(
                    "Adding this type of devices is allowed only via "
                    "Assets module."
                )
        return cleaned_data


class ProcessorInline(ForeignKeyAutocompleteTabularInline):
    model = models.Processor
    # readonly_fields = ('label', 'index', 'speed')
    exclude = ('created', 'modified')
    extra = 0
    related_search_fields = {
        'model': ['^name'],
    }


class MemoryInline(ForeignKeyAutocompleteTabularInline):
    model = models.Memory
    exclude = ('created', 'modified')
    extra = 0
    related_search_fields = {
        'model': ['^name'],
    }


class EthernetInline(ForeignKeyAutocompleteTabularInline):
    model = models.Ethernet
    exclude = ('created', 'modified')
    extra = 0
    related_search_fields = {
        'model': ['^name'],
    }


class StorageInline(ForeignKeyAutocompleteTabularInline):
    model = models.Storage
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


class InboundConnectionInline(ForeignKeyAutocompleteTabularInline):
    model = models.Connection
    extra = 1
    related_search_fields = {
        'outbound': ['^name']
    }
    fk_name = 'inbound'
    verbose_name = _("Inbound Connection")
    verbose_name_plural = _("Inbound Connections")


class OutboundConnectionInline(ForeignKeyAutocompleteTabularInline):
    model = models.Connection
    extra = 1
    related_search_fields = {
        'inbound': ['^name'],
    }
    fk_name = 'outbound'
    verbose_name = _("Outbound Connection")
    verbose_name_plural = _("Outbound Connections")


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
        InboundConnectionInline,
        OutboundConnectionInline,
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

    def get_readonly_fields(self, request, obj=None):
        ro_fields = super(DeviceAdmin, self).get_readonly_fields(request, obj)
        if obj and obj.get_asset():
            ro_fields = ro_fields + ('parent', 'management',)
        return ro_fields

    def save_model(self, request, obj, form, change):
        obj.save(user=request.user, sync_fields=True, priority=SAVE_PRIORITY)

    def save_formset(self, request, form, formset, change):
        if formset.model.__name__ == 'RolePropertyValue':
            for instance in formset.save(commit=False):
                instance.save(user=request.user)
        elif formset.model.__name__ == 'IPAddress':
            for instance in formset.save(commit=False):
                if not instance.id:
                    # Sometimes IP address exists and does not have any
                    # assigned device. In this case we should reuse it,
                    # otherwise we can get IntegrityError.
                    try:
                        ip_id = models.IPAddress.objects.filter(
                            address=instance.address,
                        ).values_list('id', flat=True)[0]
                    except IndexError:
                        pass
                    else:
                        instance.id = ip_id
                instance.save()
        else:
            formset.save(commit=True)

admin.site.register(models.Device, DeviceAdmin)


class IPAliasInline(admin.TabularInline):
    model = models.IPAlias
    exclude = ('created', 'modified')
    extra = 0


class IPAddressForm(forms.ModelForm):

    class Meta:
        model = models.IPAddress

    def clean(self):
        cleaned_data = super(IPAddressForm, self).clean()
        device = cleaned_data.get('device')
        if device and (
            'device' in self.changed_data or
            'is_management' in self.changed_data
        ):
            is_management = cleaned_data.get('is_management', False)
            if is_management and device.management_ip:
                msg = 'This device already has management IP.'
                self._errors['device'] = self.error_class([msg])
        return cleaned_data


class IPAddressAdmin(ModelAdmin):
    form = IPAddressForm
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

admin.site.register(models.IPAddress, IPAddressAdmin)


class DeprecationKindAdmin(ModelAdmin):
    save_on_top = True
    list_display = ('name', 'months', 'default')
admin.site.register(models.DeprecationKind, DeprecationKindAdmin)


class MarginKindAdmin(ModelAdmin):
    save_on_top = True
admin.site.register(models.MarginKind, MarginKindAdmin)


class LoadBalancerTypeAdmin(ModelAdmin):
    pass

admin.site.register(
    models.LoadBalancerType,
    LoadBalancerTypeAdmin,
)


class LoadBalancerVirtualServerAdmin(ModelAdmin):
    related_search_fields = {
        'device': ['^name'],
    }

admin.site.register(
    models.LoadBalancerVirtualServer,
    LoadBalancerVirtualServerAdmin,
)


class LoadBalancerMemberAdmin(ModelAdmin):
    pass

admin.site.register(
    models.LoadBalancerMember,
    LoadBalancerMemberAdmin,
)


class ComponentModelInline(admin.TabularInline):
    model = models.ComponentModel
    exclude = ('created', 'modified')
    extra = 0


class ComponentModelAdmin(ModelAdmin):

    def count(self):
        return self.get_count()

    list_filter = ('type',)
    list_display = ('name', 'type', count, 'family',)
    search_fields = ('name', 'type', 'group__name', 'family')

admin.site.register(models.ComponentModel, ComponentModelAdmin)


class GenericComponentAdmin(ModelAdmin):
    search_fields = ('label', 'sn', 'model__name')
    list_display = ('label', 'model', 'sn')
    related_search_fields = {
        'device': ['^name'],
        'model': ['^name']
    }

admin.site.register(models.GenericComponent, GenericComponentAdmin)


class DiskShareMountInline(ForeignKeyAutocompleteTabularInline):
    model = models.DiskShareMount
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

admin.site.register(models.DiskShare, DiskShareAdmin)


class HistoryChangeAdmin(ModelAdmin):
    list_display = ('date', 'user', 'device', 'component', 'field_name',
                    'old_value', 'new_value')
    list_per_page = 250
    readonly_fields = ('date', 'device', 'user', 'field_name', 'new_value',
                       'old_value', 'component')
    search_fields = ('user__username', 'field_name', 'new_value')

admin.site.register(models.HistoryChange, HistoryChangeAdmin)


class DeviceEnvironmentAdmin(ModelAdmin):
    save_on_top = True
    list_display = ('name',)
    search_fields = ('name',)


admin.site.register(models_device.DeviceEnvironment, DeviceEnvironmentAdmin)


class DatabaseTypeAdmin(ModelAdmin):
    pass

admin.site.register(
    models.DatabaseType,
    DatabaseTypeAdmin,
)


class DatabaseAdmin(ModelAdmin):
    list_filter = ('database_type__name',)
    list_display = ('name', 'venture', 'service', 'device_environment', 'database_type')
    search_fields = ('name', 'venture', 'service')
    related_search_fields = {
        'parent_device': ['^name'],
    }

admin.site.register(
    models.Database,
    DatabaseAdmin,
)
