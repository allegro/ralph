# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db.models import Count, Prefetch
from django.utils.translation import ugettext_lazy as _

from ralph.admin import RalphAdmin, RalphAdminForm, RalphTabularInline, register
from ralph.admin.filters import BaseObjectHostnameFilter, TagsListFilter
from ralph.assets.models import BaseObject
from ralph.assets.models.components import Ethernet
from ralph.assets.views import ComponentsAdminView, RalphDetailViewAdmin
from ralph.configuration_management.views import (
    SCMCheckInfo,
    SCMStatusCheckInChangeListMixin
)
from ralph.data_center.admin import generate_list_filter_with_common_fields
from ralph.data_center.models.physical import DataCenterAsset
from ralph.data_center.models.virtual import BaseObjectCluster
from ralph.deployment.mixins import ActiveDeploymentMessageMixin
from ralph.lib.custom_fields.admin import CustomFieldValueAdminMixin
from ralph.lib.transitions.admin import TransitionAdminMixin
from ralph.licences.models import BaseObjectLicence
from ralph.networks.forms import SimpleNetworkForm
from ralph.networks.views import NetworkView
from ralph.security.views import ScanStatusInChangeListMixin, SecurityInfo
from ralph.virtual.forms import CloudProviderForm
from ralph.virtual.models import (
    CloudFlavor,
    CloudHost,
    CloudProject,
    CloudProvider,
    VirtualServer,
    VirtualServerType
)

if settings.ENABLE_DNSAAS_INTEGRATION:
    from ralph.dns.views import DNSView

    class VirtualServerDNSView(DNSView):
        namespace = None


class VirtaulServerSecurityInfoView(SecurityInfo):
    url_name = 'security_virtualserver_security_info'


class CloudHostSecurityInfoView(SecurityInfo):
    url_name = 'security_cloudhost_security_info'


@register(VirtualServerType)
class VirtualServerTypeForm(RalphAdmin):
    pass


class VirtualServerForm(RalphAdminForm):
    HYPERVISOR_TYPE_ERR_MSG = _(
        'Hypervisor must be one of DataCenterAsset or CloudHost'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'parent' in self.fields:
            self.fields['parent'].required = True

    def clean_parent(self):
        value = self.cleaned_data.get('parent')
        self._validate_parent_type(value)
        return value

    def _validate_parent_type(self, value):
        allowed_types = ContentType.objects.get_for_models(
            DataCenterAsset,
            CloudHost
        ).values()
        if value.content_type not in allowed_types:
            raise ValidationError(self.HYPERVISOR_TYPE_ERR_MSG)

    class Meta:
        labels = {'parent': _('Hypervisor')}


class VirtualServerNetworkView(NetworkView):
    pass


class VirtualServerComponentsView(ComponentsAdminView):
    pass


class VirtualServerLicencesView(RalphDetailViewAdmin):
    icon = 'key'
    name = 'virtual_licences'
    label = _('Licences')
    url_name = 'licences'

    class VirtualServerLicenceInline(RalphTabularInline):
        model = BaseObjectLicence
        raw_id_fields = ('licence',)
        extra = 1

    inlines = [VirtualServerLicenceInline]


class VirtualServerSCMInfo(SCMCheckInfo):
    url_name = 'virtualserver_scm_info'


@register(VirtualServer)
class VirtualServerAdmin(
    SCMStatusCheckInChangeListMixin,
    ScanStatusInChangeListMixin,
    ActiveDeploymentMessageMixin,
    CustomFieldValueAdminMixin,
    TransitionAdminMixin,
    RalphAdmin
):
    form = VirtualServerForm
    search_fields = ['hostname', 'sn', 'ethernet_set__ipaddress__hostname']
    list_filter_prefix = [BaseObjectHostnameFilter]
    list_filter_postfix = ['sn', 'parent', TagsListFilter]
    list_filter = generate_list_filter_with_common_fields(
        list_filter_prefix,
        list_filter_postfix
    )
    list_display = [
        'hostname', 'type', 'sn', 'service_env', 'configuration_path',
        'get_parent', 'scan_status', 'scm_status_check'
    ]
    raw_id_fields = ['parent', 'service_env', 'configuration_path']
    fields = [
        'hostname', 'type', 'status', 'sn', 'service_env',
        'configuration_path', 'parent', 'remarks', 'tags'
    ]
    list_select_related = [
        'service_env__service', 'service_env__environment', 'type',
        'configuration_path__module',
    ]

    change_views = [
        VirtualServerComponentsView,
        VirtualServerNetworkView,
        VirtualServerSCMInfo,
        VirtaulServerSecurityInfoView,
        VirtualServerLicencesView,
    ]
    if settings.ENABLE_DNSAAS_INTEGRATION:
        change_views += [VirtualServerDNSView]

    show_transition_history = True

    # TODO: add the same tabs as in DCAsset
    class ClusterBaseObjectInline(RalphTabularInline):
        model = BaseObjectCluster
        fk_name = 'base_object'
        raw_id_fields = ('cluster',)
        extra = 1
        verbose_name = _('Base Object')

    inlines = [ClusterBaseObjectInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related(
            Prefetch(
                'parent',
                queryset=BaseObject.polymorphic_objects.all()
            ),
        )

    def get_parent(self, obj):
        if not obj.parent_id:
            return '-'
        return '<a href="{}">{}</a>'.format(
            obj.parent.get_absolute_url(), obj.parent.hostname
        )
    get_parent.short_description = _('Parent')
    get_parent.allow_tags = True


class CloudHostTabularInline(RalphTabularInline):
    can_delete = False
    model = CloudHost
    fk_name = 'parent'
    fields = ['get_hostname', 'get_hypervisor', 'get_ip_addresses', 'created',
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

    def get_ip_addresses(self, obj):
        ips = obj.ethernet_set.values_list(
            'ipaddress__address', flat=True
        )
        if not ips:
            return '&ndash;'
        return '\n'.join(ips)
    get_ip_addresses.short_description = _('IP Addresses')
    get_ip_addresses.allow_tags = True

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).select_related(
            'hypervisor',
        ).prefetch_related('tags')


class CloudHostNetworkForm(SimpleNetworkForm):
    class Meta(SimpleNetworkForm.Meta):
        fields = ['address', 'hostname']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['address', 'hostname']:
            self.fields[field].widget.attrs['readonly'] = True


class CloudNetworkInline(RalphTabularInline):
    can_delete = False
    form = CloudHostNetworkForm
    model = Ethernet

    def has_add_permission(self, request, obj=None):
        return False


class CloudHostNetworkView(NetworkView):
    pass


class CloudHostSCMInfo(SCMCheckInfo):
    url_name = 'cloudhost_scm_info'


@register(CloudHost)
class CloudHostAdmin(
    SCMStatusCheckInChangeListMixin, ScanStatusInChangeListMixin,
    CustomFieldValueAdminMixin, RalphAdmin
):
    list_display = ['hostname', 'get_ip_addresses', 'service_env',
                    'get_cloudproject', 'cloudflavor_name', 'host_id',
                    'created', 'image_name', 'get_tags', 'scan_status',
                    'scm_status_check']
    list_filter_prefix = [BaseObjectHostnameFilter]
    list_filter_postfix = [
        'cloudprovider', 'cloudflavor', TagsListFilter, 'hypervisor'
    ]
    list_filter = generate_list_filter_with_common_fields(
        list_filter_prefix,
        list_filter_postfix
    )
    list_select_related = [
        'cloudflavor', 'cloudprovider', 'parent__cloudproject',
        'service_env__service', 'service_env__environment'
    ]
    readonly_fields = ['cloudflavor_name', 'created', 'hostname', 'host_id',
                       'get_cloudproject', 'get_cloudprovider', 'get_service',
                       'get_cpu', 'get_disk', 'get_hypervisor', 'get_memory',
                       'modified', 'parent', 'service_env', 'image_name']
    search_fields = [
        'cloudflavor__name', 'host_id',
        'hostname', 'ethernet_set__ipaddress__hostname'
    ]
    raw_id_override_parent = {'parent': CloudProject}
    inlines = [CloudNetworkInline]
    change_views = [
        CloudHostNetworkView,
        CloudHostSCMInfo,
        CloudHostSecurityInfoView
    ]
    fieldsets = (
        (None, {
            'fields': ['hostname', 'get_hypervisor', 'host_id', 'created',
                       'get_cloudprovider', 'tags', 'remarks']
        }),
        ('Cloud Project', {
            'fields': ['get_cloudproject', 'get_service'],
        }),
        ('Components', {
            'fields': ['cloudflavor_name', 'get_cpu', 'get_memory', 'get_disk',
                       'image_name']
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            'tags',
            'ethernet_set__ipaddress'
        )

    def has_delete_permission(self, request, obj=None):
        return False

    # additional list and details fields
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
        ips = [
            eth.ipaddress.address
            for eth in obj.ethernet_set.all()
            if eth.ipaddress
        ]
        if not ips:
            return '&ndash;'
        return '\n'.join(ips)
    get_ip_addresses.short_description = _('IP Addresses')
    get_ip_addresses.allow_tags = True

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
    get_cloudproject._permission_field = 'parent'

    def get_service(self, obj):
        if obj.service_env_id:
            return '<a href="{}">{}</a>'.format(
                reverse(
                    "admin:assets_service_change",
                    args=(obj.service_env.service_id,)
                ),
                obj.service_env
            )
        return ''
    get_service.short_description = _('Service env')
    get_service.admin_order_field = 'service_env'
    get_service.allow_tags = True
    get_service._permission_field = 'service_env'

    def get_cpu(self, obj):
        return obj.cloudflavor.cores
    get_cpu.short_description = _('vCPU cores')

    def get_memory(self, obj):
        return obj.cloudflavor.memory
    get_memory.short_description = _('RAM size (MiB)')

    def get_disk(self, obj):
        return obj.cloudflavor.disk / 1024 if obj.cloudflavor.disk else None
    get_disk.short_description = _('Disk size (GiB)')


@register(CloudFlavor)
class CloudFlavorAdmin(RalphAdmin):
    list_display = ['name', 'flavor_id', 'cores', 'memory', 'disk', 'get_tags',
                    'instances_count']
    search_fields = ['name']
    readonly_fields = ['name', 'cloudprovider', 'flavor_id', 'cores',
                       'memory', 'disk', 'instances_count']
    list_filter = ['cloudprovider', TagsListFilter]
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
            'virtualcomponent_set__model', 'tags'
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
        return obj.disk / 1024
    get_disk.short_description = _('Disk size (GiB)')

    def instances_count(self, obj):
        return obj.instances_count
    instances_count.short_description = _('instances count')
    instances_count.admin_order_field = 'instances_count'


@register(CloudProject)
class CloudProjectAdmin(CustomFieldValueAdminMixin, RalphAdmin):
    fields = ['name', 'project_id', 'cloudprovider', 'service_env', 'tags',
              'remarks', 'instances_count']
    list_display = ['name', 'service_env', 'instances_count']
    list_select_related = ['cloudprovider__name', 'service_env__environment',
                           'service_env__service']
    list_filter = ['service_env', 'cloudprovider', TagsListFilter]
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
    form = CloudProviderForm
    list_display = ['name', 'cloud_sync_enabled', 'cloud_sync_driver']
    list_filter = ['name', 'cloud_sync_enabled', 'cloud_sync_driver']
