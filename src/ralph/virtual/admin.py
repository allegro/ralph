# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphAdmin, RalphTabularInline, register
from ralph.data_center.models.networks import IPAddress
from ralph.data_center.models.physical import DataCenterAsset
from ralph.virtual.models import (
    CloudFlavor,
    CloudHost,
    CloudProject,
    CloudProvider,
    VirtualServer
)


@register(VirtualServer)
class VirtualServerAdmin(RalphAdmin):
    pass


class CloudHostTabularInline(RalphTabularInline):
    can_delete = False
    model = CloudHost
    fk_name = 'parent'
    fields = ['get_hostname', 'get_hypervisor', 'get_ipaddresses', 'created',
              'tags', 'remarks']
    readonly_fields = ['created', 'get_hostname', 'get_hypervisor',
                       'get_ipaddresses', 'host_id']

    def get_hostname(self, obj):
        return '<a href="{}">{}</a>'.format(
            reverse("admin:virtual_cloudhost_change", args=(obj.id,)),
            obj.hostname
        )
    get_hostname.short_description = _('Hostname')
    get_hostname.allow_tags = True

    def get_hypervisor(self, obj):
        if obj.hypervisor is None:
            return _('Not set')
        return '<a href="{}">{}</a>'.format(
            reverse("admin:data_center_datacenterasset_change",
                    args=(obj.hypervisor.id,)),
            DataCenterAsset.objects.get(pk=obj.hypervisor).hostname
        )
    get_hypervisor.short_description = _('Hypervisor')
    get_hypervisor.allow_tags = True

    def get_ipaddresses(self, obj):
        return '\n'.join(obj.ip_addresses)
    get_ipaddresses.short_description = _('IP Addresses')

    def has_add_permission(self, request, obj=None):
        return False


class CloudNetworkInline(RalphTabularInline):
    can_delete = False
    readonly_fields = fields = ['address', 'hostname']
    model = IPAddress

    def has_add_permission(self, request, obj=None):
        return False


@register(CloudHost)
class CloudHostAdmin(RalphAdmin):
    list_display = ['hostname', 'get_ip_addresses', 'get_hypervisor',
                    'get_cloudproject', 'get_cloudprovider',
                    'cloudflavor_name', 'host_id', 'created']
    list_filter = ['hostname', 'ipaddress__address', 'service_env',
                   'cloudflavor__name', 'host_id']
    # TODO: howto cache parent__name?
    list_select_related = ['cloudflavor__name', 'cloudprovider__name',
                           'hypervisor__hostname']
    readonly_fields = ['cloudflavor_name', 'created', 'hostname', 'host_id',
                       'get_cloudproject', 'get_cloudprovider',
                       'get_cpu', 'get_disk', 'get_hypervisor', 'get_memory',
                       'modified', 'parent', 'service_env']
    search_fields = ['cloudflavor__name', 'hostname', 'host_id',
                     'ipaddress__address']
    raw_id_override_parent = {'parent': CloudProject}
    inlines = [CloudNetworkInline]
    fieldsets = (
        (None, {
            'fields': ['hostname', 'get_hypervisor', 'host_id', 'created',
                       'get_cloudprovider', 'tags', 'remarks']
        }),
        ('Cloud Project', {
            'fields': ['get_cloudproject', 'service_env'],
        }),
        ('Components', {
            'fields': ['cloudflavor_name', 'get_cpu', 'get_memory', 'get_disk']
        }),
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def get_cloudprovider(self, obj):
        return obj.cloudprovider.name
    get_cloudprovider.short_description = _('Cloud provider')
    get_cloudprovider.admin_order_field = 'cloudprovider__name'

    def get_hostname(self, obj):
        return '<a href="{}">{}</a>'.format(
            reverse("admin:virtual_cloudhost_change", args=(obj.id,)),
            obj.hostname
        )
    get_hostname.short_description = _('Hostname')
    get_hostname.allow_tags = True

    def get_hypervisor(self, obj):
        if obj.hypervisor is None:
            return _('Not set')
        return '<a href="{}">{}</a>'.format(
            reverse("admin:data_center_datacenterasset_change",
                    args=(obj.hypervisor.id,)),
            obj.hypervisor.hostname
        )
    get_hypervisor.short_description = _('Hypervisor')
    get_hypervisor.admin_order_field = 'hypervisor__hostname'
    get_hypervisor.allow_tags = True

    def cloudflavor_name(self, obj):
        return '<a href="{}">{}</a>'.format(
            reverse("admin:virtual_cloudflavor_change",
                    args=(obj.cloudflavor.id,)),
            obj.cloudflavor.name
        )
    cloudflavor_name.short_description = _('Cloud Flavor')
    cloudflavor_name.admin_order_field = 'cloudflavor__name'
    cloudflavor_name.allow_tags = True

    def get_ip_addresses(self, obj):
        return ', '.join(obj.ip_addresses)
    get_ip_addresses.short_description = _('IP Addresses')

    def get_cloudproject(self, obj):
        return '<a href="{}">{}</a>'.format(
            reverse("admin:virtual_cloudproject_change",
                    args=(obj.parent.id,)),
            CloudProject.objects.get(pk=obj.parent).name
        )
    get_cloudproject.short_description = _('Cloud Project')
    get_cloudproject.admin_order_field = 'parent'
    get_cloudproject.allow_tags = True

    def get_cpu(self, obj):
        return obj.cloudflavor.cores
    get_cpu.short_description = _('vCPU cores')

    def get_memory(self, obj):
        return obj.cloudflavor.memory
    get_memory.short_description = _('RAM size (MiB)')

    def get_disk(self, obj):
        return obj.cloudflavor.disk/1024
    get_disk.short_description = _('Disk size (GiB)')


@register(CloudFlavor)
class CloudFlavorAdmin(RalphAdmin):
    list_display = ['name', 'get_cloudprovider', 'flavor_id']
    list_select_related = ['cloudprovider__name']
    readonly_fields = ['name', 'cloudprovider', 'flavor_id', 'cores',
                       'get_memory', 'get_disk']
    fieldsets = (
        ('Cloud Flavor', {
            'fields': ['name', 'cloudprovider', 'flavor_id']
        }),
        ('Components', {
            'fields': ['cores', 'get_memory', 'get_disk']
        }),
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def get_cloudprovider(self, obj):
        return obj.cloudprovider.name
    get_cloudprovider.short_description = _('Cloud provider')
    get_cloudprovider.admin_order_field = 'cloudprovider__name'

    def get_cpu(self, obj):
        return obj.cores
    get_cpu.short_description = _('vCPU cores')

    def get_memory(self, obj):
        return obj.memory
    get_memory.short_description = _('RAM size (MiB)')

    def get_disk(self, obj):
        return obj.disk/1024
    get_disk.short_description = _('Disk size (GiB)')


@register(CloudProject)
class CloudProjectAdmin(RalphAdmin):
    fields = ['name', 'project_id', 'cloudprovider', 'service_env', 'tags',
              'remarks']
    list_display = ['name', 'service_env', 'get_cloudprovider']
    list_select_related = ['cloudprovider__name', 'service_env__environment',
                           'service_env__service']
    list_filter = ['name', 'project_id', 'service_env', 'cloudprovider__name']
    readonly_fields = ['name', 'project_id', 'cloudprovider', 'created']
    search_fields = ['name', 'project_id', 'cloudprovider__name']
    raw_id_fields = ['service_env']
    inlines = [CloudHostTabularInline]

    def has_delete_permission(self, request, obj=None):
        return False

    def get_cloudprovider(self, obj):
        return obj.cloudprovider.name
    get_cloudprovider.short_description = _('Cloud provider')
    get_cloudprovider.admin_order_field = 'cloudprovider__name'


@register(CloudProvider)
class CloudProviderAdmin(RalphAdmin):
    pass
