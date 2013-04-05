from django.contrib.auth.decorators import login_required
from django.conf.urls.defaults import patterns, include, url
from django.views.generic import RedirectView
from tastypie.api import Api
from ralph.business.api import (
    DepartmentResource,
    RoleLightResource,
    RolePropertyResource,
    RolePropertyTypeResource,
    RolePropertyTypeValueResource,
    RolePropertyValueResource,
    RoleResource,
    VentureLightResource,
    VentureResource,
)
from ralph.deployment.api import DeploymentResource
from ralph.discovery.api import (
    BladeServerResource,
    DeviceWithPricingResource,
    DevResource,
    IPAddressResource,
    ModelGroupResource,
    ModelResource,
    PhysicalServerResource,
    RackServerResource,
    VirtualServerResource,
)
from ralph.cmdb.api import (
    BusinessLineResource,
    CIChangeCMDBHistoryResource,
    CIChangeGitResource,
    CIChangePuppetResource,
    CIChangeResource,
    CIChangeZabbixTriggerResource,
    CILayersResource,
    CIOwnersResource,
    CIRelationResource,
    CIResource,
    CITypesResource,
    ServiceResource,
)
from ralph.discovery.api_donpedro import WindowsDeviceResource
from ralph.ui.views.common import VhostRedirectView

from django.conf import settings
from django.contrib import admin
from ajax_select import urls as ajax_select_urls

admin.autodiscover()

v09_api = Api(api_name='v0.9')
OPTIONAL_APPS = ['ralph_assets', ]
# business API
for r in (VentureResource, VentureLightResource, RoleResource,
          RoleLightResource, DepartmentResource, RolePropertyTypeResource,
          RolePropertyTypeValueResource, RolePropertyResource,
          RolePropertyValueResource):
    v09_api.register(r())

# discovery API
for r in (IPAddressResource, ModelGroupResource, ModelResource,
          PhysicalServerResource, RackServerResource, BladeServerResource,
          VirtualServerResource, DevResource, WindowsDeviceResource,
          DeviceWithPricingResource):
    v09_api.register(r())

# CMDB API
for r in (BusinessLineResource, ServiceResource, CIResource,
          CIRelationResource, CIChangeResource, CIChangeGitResource,
          CIOwnersResource, CIChangePuppetResource, CIChangeZabbixTriggerResource,
          CIChangeCMDBHistoryResource, CITypesResource, CILayersResource):
    v09_api.register(r())

# deployment API
for r in (DeploymentResource,):
    v09_api.register(r())


urlpatterns = patterns(
    '',
    url(r'^$', login_required(VhostRedirectView.as_view(permanent=False))),
    url(r'^report-a-bug$', RedirectView.as_view(url=settings.BUGTRACKER_URL)),
    url(r'^favicon\.ico$',
        RedirectView.as_view(url='/static/img/favicon.ico')),
    url(r'^humans\.txt$', RedirectView.as_view(url='/static/humans.txt')),
    url(r'^robots\.txt$', RedirectView.as_view(url='/static/robots.txt')),
    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': settings.STATIC_ROOT, 'show_indexes': True}),
    (r'^u/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    url(r'^login/', 'django.contrib.auth.views.login',
        {'template_name': 'admin/login.html'}),
    url(r'^logout/', 'django.contrib.auth.views.logout'),  # {'template_name': 'admin/logout.html'}),
    url(r'^ventures/(?P<venture_id>.+)/$',
        'ralph.business.views.show_ventures',
        name='business-show-venture'),
    url(r'^ventures/$', 'ralph.business.views.show_ventures',
        name='business-show-ventures'),
    url(r'^browse/$', RedirectView.as_view(url='/ui/racks/')),
    url(r'^business/$', RedirectView.as_view(url='/ui/ventures/-/venture/')),
    url(r'^business/ventures/$', RedirectView.as_view(url='/ventures/')),
    url(r'^findme/$', RedirectView.as_view(url='/ui/search/info/')),
    url(r'^catalog/$', RedirectView.as_view(url='/ui/catalog/')),
    url(r'^warnings/$', RedirectView.as_view(url='/ui/catalog/')),
    url(r'^integration/', include('ralph.integration.urls')),
    url(r'^ui/', include('ralph.ui.urls')),
    url(r'^dns/', include('ralph.dnsedit.urls')),
    url(r'^dhcp-synch/', 'ralph.dnsedit.views.dhcp_synch'),
    url(r'^dhcp-config/', 'ralph.dnsedit.views.dhcp_config'),
    url(r'^cmdb/', include('ralph.cmdb.urls')),
    url(r'^api/', include(v09_api.urls)),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^pxe/_(?P<file_type>[^/]+)$',
        'ralph.deployment.views.preboot_type_view', name='preboot-type-view'),
    url(r'^pxe/(?P<file_name>[^_][^/]+)$',
        'ralph.deployment.views.preboot_raw_view', name='preboot-raw-view'),
    url(r'^pxe/$', 'ralph.deployment.views.preboot_type_view',
        name='preboot-default-view', kwargs={'file_type': 'boot_ipxe'}),
    url(r'^pxe/DONE/$', 'ralph.deployment.views.preboot_complete_view',
        name='preboot-complete-view'),
    url(r'^puppet-classifier/$', 'ralph.deployment.views.puppet_classifier',
        name='puppet-classifier'),
    url(r'^rq/', include('django_rq.urls')),
    url(r'^user/', include('ralph.account.urls')),
    # include the lookup urls
    (r'^admin/lookups/', include(ajax_select_urls)),
    (r'^admin/', include(admin.site.urls)),

)

for app in settings.INSTALLED_APPS:
    if app in OPTIONAL_APPS:
        app_urls = url(r'^{}/'.format(app[6:]), include('{}.urls'.format(app)))
        urlpatterns.append(app_urls)
