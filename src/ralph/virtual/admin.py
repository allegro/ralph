# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse

from ralph.admin import RalphAdmin, RalphTabularInline, register
from ralph.data_center.models.networks import IPAddress
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
    fields = ['get_hostname', 'host_id', 'tags', 'remarks']
    readonly_fields = ['get_hostname', 'host_id']

    def get_hostname(self, obj):
        return '<a href="{}">{}</a>'.format(
            reverse("admin:virtual_cloudhost_change", args=(obj.id,)),
            obj.hostname
        )
    get_hostname.short_description = 'Hostname'
    get_hostname.allow_tags = True

    def has_add_permission(self, request, obj=None):
        return False


class CloudNetworkInLine(RalphTabularInline):
    can_delete = False
    readonly_fields = fields = ['address', 'hostname']
    model = IPAddress

    def has_add_permission(self, request, obj=None):
        return False


@register(CloudHost)
class CloudHostAdmin(RalphAdmin):
    list_display = ['hostname', 'get_ips', 'get_cloudproject',
                    'cloudflavor_name', 'host_id', 'created']
    list_filter = ['hostname', 'ipaddress__address', 'service_env',
                   'cloudflavor__name', 'host_id']
    readonly_fields = ['cloudflavor_name', 'created', 'hostname', 'host_id',
                       'get_cloudproject', 'get_cpu', 'get_disk', 'get_memory',
                       'modified', 'parent', 'service_env']
    # TODO: How to add a search by a field name of the class cloudproject
    search_fields = ['cloudflavor__name', 'hostname', 'host_id',
                     'ipaddress__address']
    inlines = [CloudNetworkInLine]
    fieldsets = (
        (None, {
            'fields': ['hostname', 'host_id', 'created', 'tags',
                       'remarks']
        }),
        ('Cloud Project', {
            'fields': ['get_cloudproject', 'service_env'],
        }),
        ('Components', {
            'fields': ['cloudflavor_name', 'get_cpu', 'get_memory', 'get_disk']
        }),
    )

    def get_cloudproject(self, obj):
        return '<a href="{}">{}</a>'.format(
            reverse("admin:virtual_cloudproject_change",
                    args=(obj.parent.id,)),
            CloudProject.objects.get(pk=obj.parent).name
        )
    get_cloudproject.short_description = 'Cloud Project'
    get_cloudproject.allow_tags = True

    def cloudflavor_name(self, obj):
        return '<a href="{}">{}</a>'.format(
            reverse("admin:virtual_cloudflavor_change",
                    args=(obj.cloudflavor.id,)),
            obj.cloudflavor.name
        )
    cloudflavor_name.short_description = 'Cloud Flavor'
    cloudflavor_name.allow_tags = True

    def get_ips(self, obj):
        ips = []
        for ip in IPAddress.objects.filter(base_object=obj):
            ips.append(ip.address)
        return ', '.join(ips)
    get_ips.short_description = 'IP address(es)'

    def get_cpu(self, obj):
        return obj.cloudflavor.cores
    get_cpu.short_description = 'vCPU cores'

    def get_memory(self, obj):
        return obj.cloudflavor.memory
    get_memory.short_description = 'RAM size (MiB)'

    def get_disk(self, obj):
        return obj.cloudflavor.disk/1024
    get_disk.short_description = 'Disk size (GiB)'


@register(CloudFlavor)
class CloudFlavorAdmin(RalphAdmin):
    list_display = ['name', 'get_cloudprovider', 'flavor_id']
    readonly_fields = ['name', 'cloudprovider', 'flavor_id', 'get_cpu',
                       'get_memory', 'get_disk']
    fieldsets = (
        ('Cloud Flavor', {
            'fields': ['name', 'cloudprovider', 'flavor_id']
        }),
        ('Components', {
            'fields': ['get_cpu', 'get_memory', 'get_disk']
        }),
    )

    def get_cloudprovider(self, obj):
        return obj.cloudprovider.name
    get_cloudprovider.short_description = 'Cloud provider'
    get_cloudprovider.admin_order_field = 'cloudprovider__name'

    def get_cpu(self, obj):
        return obj.cores
    get_cpu.short_description = 'vCPU cores'

    def get_memory(self, obj):
        return obj.memory
    get_memory.short_description = 'RAM size (MiB)'

    def get_disk(self, obj):
        return obj.disk/1024
    get_disk.short_description = 'Disk size (GiB)'


@register(CloudProject)
class CloudProjectAdmin(RalphAdmin):
    fields = ['name', 'project_id', 'cloudprovider', 'service_env', 'tags',
              'remarks']
    list_display = ['name', 'get_cloudprovider', 'project_id']
    list_filter = ['name', 'project_id', 'service_env', 'cloudprovider__name']
    readonly_fields = ['name', 'project_id', 'cloudprovider', 'created']
    search_fields = ['name', 'project_id', 'cloudprovider__name']
    raw_id_fields = ['service_env']
    inlines = [CloudHostTabularInline]

    def get_cloudprovider(self, obj):
        return obj.cloudprovider.name
    get_cloudprovider.short_description = 'Cloud provider'
    get_cloudprovider.admin_order_field = 'cloudprovider__name'


@register(CloudProvider)
class CloudProviderAdmin(RalphAdmin):
    pass
