# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.utils.translation import ugettext_lazy as _

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
    fields = ['get_hostname', 'get_hypervisor', 'get_ipaddresses', 'created',
              'tags', 'remarks']
    readonly_fields = fields

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
            reverse(
                "admin:data_center_datacenterasset_change",
                args=(obj.hypervisor.id,)
            ),
            obj.hypervisor.hostname
        )
    get_hypervisor.short_description = _('Hypervisor')
    get_hypervisor.allow_tags = True

    def get_ipaddresses(self, obj):
        return '\n'.join(obj.ip_addresses)
    get_ipaddresses.short_description = _('IP Addresses')

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).select_related(
            'hypervisor',
        ).prefetch_related(
            'ipaddress_set', 'tags'
        )


class CloudNetworkInline(RalphTabularInline):
    can_delete = False
    readonly_fields = fields = ['address', 'hostname']
    model = IPAddress

    def has_add_permission(self, request, obj=None):
        return False


@register(CloudHost)
class CloudHostAdmin(RalphAdmin):
    list_display = ['hostname', 'get_ip_addresses', 'service_env',
                    'get_cloudproject', 'cloudflavor_name', 'host_id',
                    'created', 'image_name', 'get_tags']
    list_filter = ['cloudprovider', 'service_env', 'cloudflavor', 'tags']
    list_select_related = [
        'cloudflavor', 'cloudprovider', 'parent__cloudproject',
        'service_env__service', 'service_env__environment'
    ]
    readonly_fields = ['cloudflavor_name', 'created', 'hostname', 'host_id',
                       'get_cloudproject', 'get_cloudprovider',
                       'get_cpu', 'get_disk', 'get_hypervisor', 'get_memory',
                       'modified', 'parent', 'service_env', 'image_name']
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
            'fields': ['cloudflavor_name', 'get_cpu', 'get_memory', 'get_disk',
                       'image_name']
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            'ipaddress_set', 'tags'
        )

    def has_delete_permission(self, request, obj=None):
        return False

    def get_tags(self, obj):
        return ', '.join([tag.name for tag in obj.tags.all()])
    get_tags.short_description = _('Tags')

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
        return '\n'.join(obj.ip_addresses)
    get_ip_addresses.short_description = _('IP Addresses')

    def get_cloudproject(self, obj):
        return '<a href="{}">{}</a>'.format(
            reverse(
                "admin:virtual_cloudproject_change",
                args=(obj.parent.id,)
            ),
            obj.parent.cloudproject.name
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
    list_display = ['name', 'flavor_id', 'cores', 'memory', 'disk', 'get_tags',
                    'instances_count']
    search_fields = ['name']
    readonly_fields = ['name', 'cloudprovider', 'flavor_id', 'cores',
                       'memory', 'disk', 'instances_count']
    list_filter = ['cloudprovider', 'tags']
    fieldsets = (
        ('Cloud Flavor', {
            'fields': ['name', 'cloudprovider', 'flavor_id', 'tags',
                       'instances_count']
        }),
        ('Components', {
            'fields': ['cores', 'memory', 'disk']
        }),
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            'virtualcomponent__model', 'tags'
        ).annotate(instances_count=Count('cloudhost'))

    def get_tags(self, obj):
        return ', '.join([tag.name for tag in obj.tags.all()])
    get_tags.short_description = _('Tags')

    def get_cpu(self, obj):
        return obj.cores
    get_cpu.short_description = _('vCPU cores')

    def get_memory(self, obj):
        return obj.memory
    get_memory.short_description = _('RAM size (MiB)')

    def get_disk(self, obj):
        return obj.disk/1024
    get_disk.short_description = _('Disk size (GiB)')

    def instances_count(self, obj):
        return obj.instances_count
    instances_count.short_description = _('instances count')
    instances_count.admin_order_field = 'instances_count'


@register(CloudProject)
class CloudProjectAdmin(RalphAdmin):
    fields = ['name', 'project_id', 'cloudprovider', 'service_env', 'tags',
              'remarks', 'instances_count']
    list_display = ['name', 'service_env', 'instances_count']
    list_select_related = ['cloudprovider__name', 'service_env__environment',
                           'service_env__service']
    list_filter = ['service_env', 'cloudprovider', 'tags']
    readonly_fields = ['name', 'project_id', 'cloudprovider', 'created',
                       'instances_count']
    search_fields = ['name', 'project_id']
    raw_id_fields = ['service_env']
    inlines = [CloudHostTabularInline]

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            instances_count=Count('children')
        )

    def get_cloudprovider(self, obj):
        return obj.cloudprovider.name
    get_cloudprovider.short_description = _('Cloud provider')
    get_cloudprovider.admin_order_field = 'cloudprovider__name'

    def instances_count(self, obj):
        return obj.instances_count
    instances_count.short_description = _('instances count')
    instances_count.admin_order_field = 'instances_count'


@register(CloudProvider)
class CloudProviderAdmin(RalphAdmin):
    pass
