# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import copy
import datetime
import ipaddr

import django_rq
import pluggableapp
import rq
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.db import models as db, transaction
from django.http import HttpResponseRedirect, HttpResponseForbidden, Http404
from django.shortcuts import get_object_or_404
from django.utils import importlib, timezone
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _
from django.views.generic import (
    DetailView,
    RedirectView,
    TemplateView,
    UpdateView,
)
from lck.django.common import nested_commit_on_success
from lck.django.tags.models import Language, TagStem
from bob.menu import MenuItem
from bob.data_table import DataTableColumn, DataTableMixin
from powerdns.models import Record

from ralph.discovery.models import ServiceCatalog, DeviceEnvironment
from ralph.discovery.models_component import Ethernet
from ralph.account.models import Perm, get_user_home_page_url, ralph_permission
from ralph.app import RalphModule
from ralph.menu import Menu
from ralph.scan.api import SCAN_RESULT_TTL
from ralph.scan.errors import Error as ScanError
from ralph.scan.manual import queue_scan_address
from ralph.scan.forms import DiffForm
from ralph.scan.data import (
    append_merged_proposition,
    device_from_data,
    find_devices,
    get_device_data,
    get_external_results_priorities,
    merge_data,
    set_device_data,
)
from ralph.scan.diff import diff_results, sort_results
from ralph.scan.models import ScanSummary
from ralph.scan.util import get_pending_changes, update_scan_summary
from ralph.business.models import (
    Venture,
    VentureRole,
)
from ralph.deployment.models import Deployment, DeploymentStatus
from ralph.deployment.util import get_next_free_hostname, get_first_free_ip
from ralph.dnsedit.models import DHCPEntry
from ralph.dnsedit.util import (
    get_domain,
    set_revdns_record,
    get_revdns_records,
    reset_dns,
    update_txt_records,
)
from ralph.dnsedit.util import Error as DNSError
from ralph.discovery.models import (
    ASSET_NOT_REQUIRED,
    ConnectionType,
    Device,
    DeviceType,
    IPAddress,
    Network,
)
from ralph.menu import menu_class as ralph_menu
from ralph.scan.data import get_choice_by_name
from ralph.util import details, presentation
from ralph.util.plugin import BY_NAME as AVAILABLE_PLUGINS
from ralph.ui.forms import ChooseAssetForm, VentureServiceFilterForm
from ralph.ui.forms.devices import (
    DeviceInfoForm,
    DeviceInfoVerifiedForm,
    PropertyForm,
    DeviceBulkForm,
)
from ralph.ui.forms.addresses import (
    DHCPFormSet,
    DNSFormSet,
    IPAddressFormSet,
    IPManagementForm,
)
from ralph.ui.forms.deployment import (
    ServerMoveStep1Form,
    ServerMoveStep2FormSet,
    ServerMoveStep3FormSet,
)
from ralph_assets.models_signals import update_core_localization


SAVE_PRIORITY = 215
HISTORY_PAGE_SIZE = 25
MAX_PAGE_SIZE = 65535
TEMPLATE_MENU_ITEMS = [
    MenuItem(
        'Manual device',
        name='device',
        fugue_icon='fugue-wooden-box',
        href='/ui/racks//add_device/',
    ),
    MenuItem(
        'Servers',
        name='servers',
        fugue_icon='fugue-computer',
        href='/ui/deployment/mass/start/',
    ),
    MenuItem(
        'Move Servers',
        name='move_servers',
        fugue_icon='fugue-computer--arrow',
        href='/ui/racks//move/',
    ),
]
CHANGELOG_URL = "http://ralph.allegrogroup.com/doc/changes.html"


def _get_balancers(dev):
    for ip in dev.ipaddress_set.all():
        for member in ip.loadbalancermember_set.select_related(
            'device__name',
            'pool__name',
        ).order_by('device'):
            yield {
                'balancer': member.device.name,
                'pool': member.pool.name,
                'enabled': member.enabled,
                'server': None,
                'port': member.port,
            }
    for vserv in dev.loadbalancervirtualserver_set.select_related(
        'default_pool__name',
    ).all():
        yield {
            'balancer': dev.name,
            'pool': vserv.default_pool.name if vserv.default_pool else None,
            'enabled': None,
            'address': vserv.address.address,
            'server': vserv.name,
            'port': vserv.port,
        }


def _get_details(dev):
    for detail in details.details_all(dev):
        if 'icon' not in detail:
            if detail['group'] == 'dev':
                detail['icon'] = presentation.get_device_model_icon(
                    detail.get('model'),
                )
            else:
                detail['icon'] = presentation.get_component_model_icon(
                    detail.get('model'),
                )
        if (
            detail['group'] != 'dev' and
            'size' not in detail and
            detail.get('model')
        ):
            detail['size'] = detail['model'].size
        if not detail.get('model'):
            detail['model'] = detail.get('model_name', '')
        yield detail


class ACLGateway(object):

    @ralph_permission()  # 'Perm.has_core_access' are used by default
    def dispatch(self, *args, **kwargs):
        return super(ACLGateway, self).dispatch(*args, **kwargs)


class AdminMenu(Menu):
    module = MenuItem(
        'Admin',
        name='admin',
        fugue_icon='fugue-toolbox',
        href='/admin/',
        pull_right=True,
    )


class UserMenu(Menu):

    def __init__(self, request, **kwargs):
        self.module = MenuItem(
            '{}'.format(request.user),
            name='user_preference',
            fugue_icon='fugue-user',
            view_name='user_preference',
            pull_right=True,
        )
        super(UserMenu, self).__init__(request, **kwargs)


class LogoutMenu(Menu):
    module = MenuItem(
        'Logout',
        name='logout',
        fugue_icon='fugue-toolbox',
        view_name='logout',
        pull_right=True,
    )


class MenuMixin(object):
    module_name = None
    submodule_name = None
    sidebar_item_name = None

    def dispatch(self, request, *args, **kwargs):
        self.menus = [ralph_menu(request)]
        self.menus.append(LogoutMenu(request))
        self.menus.append(UserMenu(request))
        if request.user.is_staff:
            self.menus.append(AdminMenu(request))
        for app in pluggableapp.app_dict.values():
            if (
                not isinstance(app, RalphModule) or
                app.module_name in settings.HIDE_MENU or
                not app.has_menu
            ):
                continue
            menu_module = importlib.import_module(
                '.'.join([app.module_name, 'menu'])
            )
            if menu_module:
                menu_class = getattr(
                    menu_module, 'menu_class', None
                )
                if not menu_class:
                    raise Exception(
                        'Please provide menu_class.'
                    )
                self.menus.append(menu_class(request))
        return super(MenuMixin, self).dispatch(request, *args, **kwargs)

    @property
    def current_menu(self):
        menu = None
        if hasattr(self, 'menus'):
            for menu in self.menus:
                if menu.module.name == self.module_name:
                    break
        return menu

    @property
    def active_module(self):
        if not self.module_name:
            raise ImproperlyConfigured(
                '{view} required definition of \'module_name\''.format(
                    view=self.__class__.__name__))
        return self.module_name

    @property
    def active_submodule(self):
        if not self.submodule_name:
            raise ImproperlyConfigured(
                '{view} required definition of \'submodule_name\''.format(
                    view=self.__class__))
        return self.submodule_name

    @property
    def active_sidebar_item(self):
        return self.sidebar_item_name

    def get_modules(self):
        if hasattr(self, 'menus'):
            main_menu = [menu.module for menu in self.menus]
        else:
            main_menu = []
        return main_menu

    def get_submodules(self):
        if self.current_menu:
            submodules = self.current_menu.get_submodules()
        else:
            submodules = None
        return submodules

    def get_context_data(self, **kwargs):
        context = super(MenuMixin, self).get_context_data(**kwargs)
        current_menu = self.current_menu
        if not current_menu:
            sidebar = None
        else:
            sidebar = current_menu.get_sidebar_items().get(
                self.active_submodule, None
            )
        context.update({
            'main_menu': self.get_modules(),
            'submodules': self.get_submodules(),
            'sidebar': sidebar,
            'active_menu': current_menu,
            'active_module': self.active_module,
            'active_submodule': self.active_submodule,
            'active_sidebar_item': self.active_sidebar_item,
        })
        return context


class BaseMixin(MenuMixin, ACLGateway):
    module_name = 'module_core'

    def __init__(self, *args, **kwargs):
        super(BaseMixin, self).__init__(*args, **kwargs)
        self.venture = None
        self.object = None
        self.status = ''

    def tab_href(self, name, obj=''):
        section = self.active_submodule
        if not obj and self.object:
            obj = self.object.id
        if section == 'racks':
            args = [self.kwargs.get('rack'), name, obj]
        elif section == 'networks':
            args = [self.kwargs.get('network'), name, obj]
        elif section == 'ventures':
            args = [self.kwargs.get('venture'), name, obj]
        elif section == 'search':
            args = [name, obj]
        elif section == 'services':
            args = []
            if self.kwargs.get('businessline_id'):
                args.append(self.kwargs['businessline_id'])
                if self.kwargs.get('service_id'):
                    args.append(self.kwargs['service_id'])
                    if self.kwargs.get('environment_id'):
                        args.append(self.kwargs['environment_id'])
            args.extend([name, obj])
        else:
            args = []
        return '%s?%s' % (
            reverse(section, args=args),
            self.request.GET.urlencode(),
        )

    def get_tab_items(self):
        details = self.kwargs.get('details', 'info')
        profile = self.request.user.get_profile()
        has_perm = profile.has_perm
        tab_items = []
        venture = (
            self.venture if self.venture and self.venture != '*' else None
        ) or (
            self.object.venture if self.object else None
        )

        if has_perm(Perm.read_device_info_generic, venture):
            tab_items.extend([
                MenuItem('Info', fugue_icon='fugue-wooden-box',
                         href=self.tab_href('info')),
                MenuItem('Components', fugue_icon='fugue-box',
                         href=self.tab_href('components')),
                MenuItem('Software', fugue_icon='fugue-disc',
                         href=self.tab_href('software')),
                MenuItem('Addresses', fugue_icon='fugue-network-ip',
                         href=self.tab_href('addresses')),
            ])
        if has_perm(Perm.read_device_info_history, venture):
            tab_items.extend([
                MenuItem('History', fugue_icon='fugue-hourglass',
                         href=self.tab_href('history')),
            ])
        if all((
            'ralph_assets' in settings.INSTALLED_APPS,
            has_perm(Perm.read_device_info_support, venture),
        )):
            tab_items.extend([
                MenuItem(
                    'Linked Asset',
                    name='asset',
                    fugue_icon='fugue-baggage-cart-box',
                    href=self.tab_href('asset')),
            ])
        if all((
            has_perm(Perm.edit_device_info_generic),
            self.kwargs.get('device') or self.kwargs.get('address'),
        )):
            tab_items.extend([
                MenuItem(
                    'Scan',
                    name='scan',
                    fugue_icon='fugue-flashlight',
                    href=self.tab_href('scan'),
                ),
            ])
        if all((
            has_perm(Perm.edit_device_info_generic, venture),
            not (self.kwargs.get('device') or self.kwargs.get('address')),
        )):
            tab_items.extend([
                MenuItem('Reports', fugue_icon='fugue-reports-stack',
                         href=self.tab_href('reports')),
            ])
        if details == 'bulkedit':
            tab_items.extend([
                MenuItem('Bulk edit', fugue_icon='fugue-pencil-field',
                         name='bulkedit'),
            ])
        return tab_items

    def get_context_data(self, **kwargs):
        ret = super(BaseMixin, self).get_context_data(**kwargs)
        details = self.kwargs.get('details', 'info')
        profile = self.request.user.get_profile()
        has_perm = profile.has_perm
        tab_items = self.get_tab_items()
        ret.update({
            'details': details,
            'url_query': self.request.GET,
            'search_url': reverse('search', args=[details, '']),
            'user': self.request.user,
            'tab_items': tab_items,
            'show_bulk': has_perm(Perm.bulk_edit),
        })
        return ret


class Base(BaseMixin, TemplateView):
    columns = []

    def get_context_data(self, **kwargs):
        ret = super(Base, self).get_context_data(**kwargs)
        ret.update({
            'columns': self.columns,
        })
        return ret


class Home(Base):
    template_name = 'ui/home.html'

    def get_context_data(self, **kwargs):
        ret = super(Home, self).get_context_data(**kwargs)
        profile = self.request.user.get_profile()
        devices = TagStem.objects.get_content_objects(author=profile)
        for d in devices:
            tags = d.get_tags(official=False, author=profile)
            tags = ['"%s"' % t.name if ',' in t.name else t.name for t in tags]
            d.tag_str = ', '.join(tags)
        ret.update({
            'devices': devices,
        })
        return ret


class DeviceUpdateView(UpdateView):
    model = Device
    slug_field = 'id'
    slug_url_kwarg = 'device'

    def get_success_url(self):
        return self.request.path

    def get_template_names(self):
        return [self.template_name]

    def get_context_data(self, **kwargs):
        ret = super(DeviceUpdateView, self).get_context_data(**kwargs)
        has_perm = self.request.user.get_profile().has_perm
        ret.update({
            'device': self.object,
            'editable': has_perm(self.edit_perm, self.object.venture),
        })
        return ret

    def form_valid(self, form):
        model = form.save(commit=False)
        model.save_comment = form.cleaned_data.get('save_comment')
        model.save(priority=SAVE_PRIORITY, user=self.request.user)
        details.device_update_name_rack_dc(model)
        messages.success(self.request, "Changes saved.")
        return HttpResponseRedirect(self.request.path)

    def form_invalid(self, form):
        messages.error(
            self.request,
            _("There are some errors in your form. See below for details.")
        )
        return super(DeviceUpdateView, self).form_invalid(form)

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        has_perm = self.request.user.get_profile().has_perm
        if not has_perm(self.read_perm, self.object.venture):
            return HttpResponseForbidden(
                "You don't have permission to see this."
            )
        return super(DeviceUpdateView, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        has_perm = self.request.user.get_profile().has_perm
        if not has_perm(self.edit_perm, self.object.venture):
            return HttpResponseForbidden(
                "You don't have permission to edit this."
            )
        return super(DeviceUpdateView, self).post(*args, **kwargs)


class DeviceDetailView(DetailView):
    model = Device
    slug_field = 'id'
    slug_url_kwarg = 'device'

    def get_template_names(self):
        return [self.template_name]

    def get_context_data(self, **kwargs):
        ret = super(DeviceDetailView, self).get_context_data(**kwargs)
        ret.update({
            'device': self.object,
        })
        return ret

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        has_perm = self.request.user.get_profile().has_perm
        if not has_perm(self.read_perm, self.object.venture):
            return HttpResponseForbidden(
                "You don't have permission to see this."
            )
        return super(DeviceDetailView, self).get(*args, **kwargs)


class Info(DeviceUpdateView):
    template_name = 'ui/device_info.html'
    read_perm = Perm.read_device_info_generic
    edit_perm = Perm.edit_device_info_generic

    def get_form_class(self):
        if self.object.verified:
            return DeviceInfoVerifiedForm
        return DeviceInfoForm

    def get_initial(self):
        return {
            'model_name': self.object.get_model_name(),
            'rack_name': self.object.rack,
            'dc_name': self.object.dc,
        }

    def get_running_deployment_info(self):
        try:
            deployment = Deployment.objects.exclude(
                status=DeploymentStatus.done,
            ).get(device=self.object)
        except Deployment.DoesNotExist:
            return False, []
        deployment_plugins = AVAILABLE_PLUGINS['deployment'].keys()
        done_plugins = [
            plugin.strip()
            for plugin in deployment.done_plugins.split(',')
            if plugin.strip()
        ]
        return DeploymentStatus.raw_from_id(deployment.status), [
            {'name': plugin, 'state': plugin in done_plugins}
            for plugin in deployment_plugins
        ]

    def get_changed_addresses(self):
        delta = timezone.now() - datetime.timedelta(days=1)
        return self.object.ipaddress.filter(
            scan_summary__modified__gt=delta,
            scan_summary__changed=True,
        )

    def get_context_data(self, **kwargs):
        ret = super(Info, self).get_context_data(**kwargs)
        if self.object:
            if 'ralph_assets' in settings.INSTALLED_APPS:
                from ralph_assets.models_assets import DeviceInfo
                assets_imported = True
            else:
                assets_imported = False
            tags = self.object.get_tags(
                official=False,
                author=self.request.user,
            )
            if self.object.dirty_fields:
                deploy_disable_reason = _(
                    "This device contains dirty fields."
                )
            elif not (
                not assets_imported or
                DeviceInfo.objects.filter(ralph_device_id=self.object.pk) or
                (
                    self.object.model and
                    self.object.model.type == DeviceType.virtual_server
                )
            ):
                deploy_disable_reason = _(
                    "This device is not linked to an asset."
                )
            elif not self.object.verified:
                deploy_disable_reason = _(
                    "This device is not verified."
                )
            else:
                deploy_disable_reason = None
        else:
            tags = []
        tags = ['"%s"' % t.name if ',' in t.name else t.name for t in tags]
        deployment_status, plugins = self.get_running_deployment_info()
        inbound_connections = self.object.inbound_connections.filter(
            connection_type=ConnectionType.network
        ).select_related(
            'inbound', 'networkconnection'
        )
        outbound_connections = self.object.outbound_connections.filter(
            connection_type=ConnectionType.network
        ).select_related(
            'outbound', 'networkconnection'
        ).order_by('connection_type')
        network_connections = []
        if inbound_connections or outbound_connections:
            network_connections = [
                ("inbound", inbound_connections),
                ("outbound", outbound_connections),
            ]
            for conn_type, conn_items in network_connections:
                for conn_item in conn_items:
                    conn_item.kind = ConnectionType.name_from_id(
                        conn_item.connection_type
                    )
        ret.update({
            'property_form': self.property_form,
            'tags': ', '.join(tags),
            'dt': DeviceType,
            'deployment_status': deployment_status,
            'plugins': plugins,
            'changed_addresses': self.get_changed_addresses(),
            'network_connections': network_connections,
            'deploy_disable_reason': deploy_disable_reason,
        })
        return ret

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        self.property_form = self.get_property_form()
        return super(Info, self).get(*args, **kwargs)

    def save_properties(self, device, properties):
        for symbol, value in properties.iteritems():
            device.set_property(symbol, value, self.request.user)

    def get_property_form(self, data=None):
        if not self.object.venture_role:
            return None
        values = self.object.venture_role.get_properties(self.object)
        if not values:
            return None
        properties = list(self.object.venture_role.roleproperty_set.all())
        properties.extend(self.object.venture.roleproperty_set.all())
        return PropertyForm(properties, data, initial=values)

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        has_perm = self.request.user.get_profile().has_perm
        if not has_perm(Perm.edit_device_info_generic, self.object.venture):
            return HttpResponseForbidden(
                "You don't have permission to edit this."
            )
        self.property_form = self.get_property_form()
        if 'propertiessave' in self.request.POST:
            self.property_form = self.get_property_form(self.request.POST)
            if self.property_form.is_valid():
                messages.success(self.request, "Properties updated.")
                self.save_properties(
                    self.object,
                    self.property_form.cleaned_data,
                )
                return HttpResponseRedirect(self.request.path)
        elif 'save-tags' in self.request.POST:
            tags = self.request.POST.get('tags', '')
            self.object.untag_all()
            self.object.tag(tags, Language.en, self.request.user)
            messages.success(self.request, "Tags updated.")
            return HttpResponseRedirect(self.request.path)
        else:
            return super(Info, self).post(*args, **kwargs)
        return super(Info, self).get(*args, **kwargs)


class Components(DeviceDetailView):
    template_name = 'ui/device_components.html'
    read_perm = Perm.read_device_info_generic

    def get_context_data(self, **kwargs):
        ret = super(Components, self).get_context_data(**kwargs)
        ret.update({'components': _get_details(self.object)})
        return ret


class Addresses(DeviceDetailView):
    template_name = 'ui/device_addresses.html'
    read_perm = Perm.read_device_info_generic
    edit_perm = Perm.edit_domain_name
    limit_types = {'A', 'CNAME', 'MX', 'TXT'}

    def __init__(self, *args, **kwargs):
        super(Addresses, self).__init__(*args, **kwargs)
        self.dns_formset = None
        self.dhcp_formset = None
        self.ip_formset = None
        self.ip_management_form = None

    def get_dns(self, limit_types=None):
        ips = set(ip.address for ip in self.object.ipaddress_set.all())
        names = set(ip.hostname for ip in self.object.ipaddress_set.all()
                    if ip.hostname)
        dotnames = set(name + '.' for name in names)
        revnames = set('.'.join(reversed(ip.split('.'))) + '.in-addr.arpa'
                       for ip in ips)
        starrevnames = set()
        for name in revnames:
            parts = name.split('.')
            while parts:
                parts.pop(0)
                starrevnames.add('.'.join(['*'] + parts))
        for entry in Record.objects.filter(
            db.Q(content__in=ips) |
            db.Q(name__in=names) |
            db.Q(content__in=names | dotnames)
        ).distinct():
            names.add(entry.name)
            if entry.type == 'A':
                ips.add(entry.content)
            elif entry.type == 'CNAME':
                names.add(entry.content)
        starnames = set()
        for name in names:
            parts = name.split('.')
            while parts:
                parts.pop(0)
                starnames.add('.'.join(['*'] + parts))
        query = Record.objects.filter(
            db.Q(content__in=ips | names) |
            db.Q(name__in=names | revnames | starnames | starrevnames)
        ).distinct().order_by('type', 'name', 'content')
        if limit_types is not None:
            query = query.filter(type__in=limit_types)
        return query

    def get_hostnames(self):
        ipaddresses = self.object.ipaddress_set.all()
        ips = set(ip.address for ip in ipaddresses)
        names = set(ip.hostname for ip in ipaddresses if ip.hostname)
        revnames = set('.'.join(reversed(ip.split('.'))) + '.in-addr.arpa'
                       for ip in ips)
        hostnames = set(names)
        for record in Record.objects.filter(
            type='A',
            content__in=ips,
        ):
            hostnames.add(record.name)
        for record in Record.objects.filter(
            type='PTR',
            name__in=revnames,
        ):
            hostnames.add(record.content.strip('.'))
        return hostnames

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        profile = self.request.user.get_profile()
        if not profile.has_perm(self.edit_perm, self.object.venture):
            return HttpResponseForbidden(
                "You don't have permission to edit this."
            )
        if 'dns' in self.request.POST:
            dns_records = self.get_dns(self.limit_types)
            ips = {ip.address for ip in self.object.ipaddress_set.all()}
            self.dns_formset = DNSFormSet(
                self.request.POST,
                queryset=dns_records,
                prefix='dns',
                hostnames=self.get_hostnames(),
                limit_types=self.limit_types,
                ips=ips,
            )
            if self.dns_formset.is_valid():
                for form in self.dns_formset.extra_forms:
                    # Bind the newly created records to domains.
                    if form.has_changed():
                        form.instance.domain = get_domain(form.instance.name)
                        # Save the user for newly added records
                        form.instance.saving_user = self.request.user
                for form in self.dns_formset.initial_forms:
                    if form.has_changed():
                        # Save the user for modified records
                        form.instance.saving_user = self.request.user
                        # Make sure the PTR record is updated on field change
                        if form.instance.ptr and (
                            'name' in form.changed_data or
                            'content' in form.changed_data
                        ):
                            r = Record.objects.get(id=form.instance.id)
                            for ptr in get_revdns_records(
                                    r.content).filter(content=r.name):
                                ptr.saving_user = self.request.user
                                ptr.delete()
                                messages.warning(
                                    self.request,
                                    "PTR record for %s and %s deleted." % (
                                        r.name,
                                        r.content,
                                    ),
                                )
                            form.changed_data.append('ptr')
                self.dns_formset.save()
                for r, data in self.dns_formset.changed_objects:
                    # Handle PTR creation/deletion
                    if 'ptr' in data:
                        if r.ptr:
                            try:
                                set_revdns_record(r.content, r.name)
                            except DNSError as e:
                                messages.error(self.request, unicode(e))
                            else:
                                messages.warning(
                                    self.request,
                                    "PTR record for %s and %s created." % (
                                        r.name,
                                        r.content,
                                    ),
                                )
                                try:
                                    ipaddress = IPAddress.objects.get(
                                        address=r.content,
                                    )
                                except IPAddress.DoesNotExist:
                                    pass
                                else:
                                    if ipaddress.device:
                                        update_txt_records(ipaddress.device)
                        else:
                            for ptr in get_revdns_records(
                                    r.content).filter(content=r.name):
                                ptr.saving_user = self.request.user
                                ptr.delete()
                                messages.warning(
                                    self.request,
                                    "PTR record for %s and %s deleted." % (
                                        r.name,
                                        r.content,
                                    ),
                                )
                for r in self.dns_formset.new_objects:
                    # Handle PTR creation
                    if r.ptr:
                        try:
                            set_revdns_record(r.content, r.name)
                        except DNSError as e:
                            messages.error(self.request, unicode(e))
                        else:
                            messages.warning(
                                self.request,
                                "PTR record for %s created." % r.content
                            )
                for r in self.dns_formset.deleted_objects:
                    # Handle PTR deletion
                    for ptr in get_revdns_records(
                            r.content).filter(content=r.name):
                        messages.warning(
                            self.request,
                            "PTR record for %s deleted." % r.name
                        )
                        ptr.saving_user = self.request.user
                        ptr.delete()
                messages.success(self.request, "DNS records updated.")
                return HttpResponseRedirect(self.request.path)
            else:
                messages.error(self.request, "Errors in the DNS form.")
                for form_errors in self.dns_formset.errors:
                    for error in form_errors.get('__all__', []):
                        messages.error(self.request, error)
                for error in self.dns_formset.non_form_errors():
                    messages.error(self.request, error)

        elif 'dhcp' in self.request.POST:
            dhcp_records = self.get_dhcp()
            macs = {e.mac for e in self.object.ethernet_set.all()}
            ips = {ip.address for ip in self.object.ipaddress_set.all()}
            self.dhcp_formset = DHCPFormSet(
                dhcp_records,
                macs,
                ips,
                self.object,
                self.request.POST,
                prefix='dhcp',
            )
            if self.dhcp_formset.is_valid():
                instances = self.dhcp_formset.save(commit=False)
                for instance in instances:
                    if not Ethernet.objects.filter(mac=instance.mac).exists():
                        Ethernet.objects.create(
                            device=self.object,
                            label=u'Ethernet',
                            mac=instance.mac,
                        )
                    instance.save()
                messages.success(self.request, "DHCP records updated.")
                return HttpResponseRedirect(self.request.path)
            else:
                messages.error(self.request, "Errors in the DHCP form.")
                for error in self.dhcp_formset.non_form_errors():
                    messages.error(self.request, error)
        elif 'ip' in self.request.POST:
            self.ip_formset = IPAddressFormSet(
                self.request.POST,
                queryset=self.object.ipaddress_set.order_by('address'),
                prefix='ip',
            )
            if self.ip_formset.is_valid():
                for form in self.ip_formset.extra_forms:
                    # Bind the newly created addresses to this device.
                    if form.has_changed():
                        IPAddress.objects.filter(
                            address=form.instance.address
                        ).delete()
                        form.instance.device = self.object
                self.ip_formset.save()
                messages.success(self.request, "IP addresses updated.")
                return HttpResponseRedirect(self.request.path)
            else:
                messages.error(self.request, "Errors in the addresses form.")
        elif 'management' in self.request.POST:
            self.ip_management_form = IPManagementForm(self.request.POST)
            if self.ip_management_form.is_valid():
                self.object.management_ip =\
                    self.ip_management_form.cleaned_data['management_ip']
                self.object.save()
                messages.success(
                    self.request, "Management IP address updated."
                )
        return self.get(*args, **kwargs)

    def get_dhcp(self):
        macs = set(eth.mac for eth in self.object.ethernet_set.all())
        return DHCPEntry.objects.filter(mac__in=macs)

    def get_context_data(self, **kwargs):
        ret = super(Addresses, self).get_context_data(**kwargs)
        if self.dns_formset is None:
            dns_records = self.get_dns(self.limit_types)
            ips = {ip.address for ip in self.object.ipaddress_set.all()}
            self.dns_formset = DNSFormSet(
                hostnames=self.get_hostnames(),
                queryset=dns_records,
                prefix='dns',
                limit_types=self.limit_types,
                ips=ips,
            )
        if self.dhcp_formset is None:
            dhcp_records = self.get_dhcp()
            macs = {e.mac for e in self.object.ethernet_set.all()}
            ips = {ip.address for ip in self.object.ipaddress_set.all()}
            self.dhcp_formset = DHCPFormSet(
                dhcp_records,
                macs,
                ips,
                self.object,
                prefix='dhcp',
            )
        if self.ip_formset is None:
            self.ip_formset = IPAddressFormSet(
                queryset=self.object.ipaddress_set.filter(
                    is_management=False
                ).order_by('address'),
                prefix='ip'
            )
        if not self.ip_management_form:
            management_ip = self.object.management_ip
            self.ip_management_form = IPManagementForm(
                initial={
                    'management_ip': (
                        management_ip and management_ip.as_tuple()
                    )
                }
            )
        profile = self.request.user.get_profile()
        can_edit = profile.has_perm(self.edit_perm, self.object.venture)
        next_hostname = None
        first_free_ip_addresses = []
        rack = self.object.find_rack()
        if rack:
            networks = rack.network_set.filter(
                environment__isnull=False,
            ).order_by('name')
            for network in networks:
                next_hostname = get_next_free_hostname(network.environment)
                if next_hostname:
                    break
            for network in networks:
                first_free_ip = get_first_free_ip(network.name)
                if first_free_ip:
                    first_free_ip_addresses.append({
                        'network_name': network.name,
                        'first_free_ip': first_free_ip,
                    })
        balancers = list(_get_balancers(self.object))
        ret.update({
            'canedit': can_edit,
            'balancers': balancers,
            'dnsformset': self.dns_formset,
            'dhcpformset': self.dhcp_formset,
            'ipformset': self.ip_formset,
            'next_hostname': next_hostname,
            'first_free_ip_addresses': first_free_ip_addresses,
            'ip_management_form': self.ip_management_form
        })
        return ret


class History(DeviceDetailView):
    template_name = 'ui/device_history.html'
    read_perm = Perm.read_device_info_history

    def get_context_data(self, **kwargs):
        query_variable_name = 'history_page'
        ret = super(History, self).get_context_data(**kwargs)
        history = self.object.historychange_set.exclude(
            field_name='snmp_community'
        ).order_by('-date')
        show_all = bool(self.request.GET.get('all', ''))
        if not show_all:
            history = history.exclude(user=None)
        try:
            page = int(self.request.GET.get(query_variable_name, 1))
        except ValueError:
            page = 1
        if page == 0:
            page = 1
        history_page = Paginator(history, HISTORY_PAGE_SIZE).page(page)
        ret.update({
            'history': history,
            'history_page': history_page,
            'show_all': show_all,
            'query_variable_name': query_variable_name,
        })
        return ret


class Asset(BaseMixin, TemplateView):
    template_name = 'ui/device_asset.html'
    form = None
    asset = None

    def get_context_data(self, **kwargs):
        ret = super(Asset, self).get_context_data(**kwargs)
        ret.update({
            'show_bulk': False,
            'device': self.object,
            'form': self.form,
            'asset': self.asset,
            'asset_required': self.asset_required,
        })
        return ret

    def get(self, *args, **kwargs):
        if 'ralph_assets' not in settings.INSTALLED_APPS:
            raise Http404()
        try:
            device_id = int(self.kwargs.get('device'))
        except (TypeError, ValueError):
            self.object = None
        else:
            self.object = get_object_or_404(Device, id=device_id)
            from ralph_assets.api_ralph import get_asset
            self.asset = get_asset(self.object.id)
            try:
                device_type = DeviceType.from_id(self.object.model.type)
            except (ValueError, AttributeError):
                device_type = None
            if device_type in ASSET_NOT_REQUIRED:
                self.asset_required = False
            else:
                self.asset_required = True
            if self.asset_required and not self.asset:
                msg = ("This device is not linked to an asset. "
                       "Please correct this using the input box below.")
                messages.warning(self.request, msg)
            if not self.form:
                self.form = ChooseAssetForm(
                    initial={
                        'asset': self.asset['asset_id'] if self.asset else None,
                    },
                    device_id=self.object.id,
                )
        return super(Asset, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        if 'ralph_assets' not in settings.INSTALLED_APPS:
            raise Http404()
        self.object = get_object_or_404(Device, id=self.kwargs.get('device'))
        self.form = ChooseAssetForm(
            data=self.request.POST,
            device_id=self.object.id,
        )
        if self.form.is_valid():
            asset = self.form.cleaned_data['asset']
            from ralph_assets.api_ralph import assign_asset
            if assign_asset(self.object.id, asset.id):
                # Deprecated. In future, localization will be stored only for
                # Asset.
                update_core_localization(asset_dev_info=asset.device_info)
                messages.success(self.request, "Asset linked successfully.")
                return HttpResponseRedirect(self.request.get_full_path())
            else:
                msg = "An error occurred. Please try again."
                messages.error(self.request, msg)
        return self.get(*args, **kwargs)


class ServerMove(BaseMixin, TemplateView):
    template_name = 'ui/bulk-move.html'
    submodule_name = 'racks'

    def __init__(self, *args, **kwargs):
        super(ServerMove, self).__init__(*args, **kwargs)
        self.form = None
        self.formset = None
        self.operations = None

    def step2_initial(self):
        addresses = [
            [ip.address for ip in self.form._get_address_candidates(a)]
            for a in self.form.cleaned_data['addresses'].split()
        ]
        for a in addresses:
            yield {
                'address': a[0],
                'network': Network.from_ip(a[0]).id,
                'candidates': a,
            }

    def step3_initial(self):
        ips = set()
        names = set()
        for f in self.formset:
            network = Network.objects.get(id=f.cleaned_data['network'])
            ip = get_first_free_ip(network.name, ips)
            ips.add(ip)
            name = get_next_free_hostname(network.environment, names)
            names.add(name)
            yield {
                'address': f.cleaned_data['address'],
                'new_ip': ip,
                'new_hostname': name,
            }

    def get_operations(self, formset):
        operations = []
        for f in formset:
            address = f.cleaned_data['address']
            new_ip = f.cleaned_data['new_ip']
            new_hostname = f.cleaned_data['new_hostname']
            mac = None
            old_ipaddress = IPAddress.objects.get(address=address)
            rev = '.'.join(
                list(reversed(new_ip.split('.')))
            ) + '.in-addr.arpa'
            operations.append((
                "warning",
                "Address %s will be deleted from device %s." % (
                    old_ipaddress.address, old_ipaddress.device
                ),
            ))
            for r in Record.objects.filter(
                    db.Q(name=old_ipaddress.hostname) |
                    db.Q(content=old_ipaddress.hostname) |
                    db.Q(content=old_ipaddress.address)
            ):
                operations.append((
                    "warning",
                    "DNS record '%s %s %s' will be deleted." % (
                        r.name, r.type, r.content
                    ),
                ))
            for e in DHCPEntry.objects.filter(ip=old_ipaddress.address):
                operations.append((
                    "warning",
                    "DHCP entry for '%s %s' will be deleted." % (
                        e.ip, e.mac
                    )
                ))
                mac = e.mac
            operations.append((
                "success",
                "Address %s will be added to device %s." % (
                    new_ip, old_ipaddress.device
                ),
            ))
            operations.append((
                "success",
                "Device %s will be renamed to %s." % (
                    old_ipaddress.device, new_hostname
                ),
            ))
            operations.append((
                "success",
                "A new DNS entry '%s A %s' will be created." % (
                    new_hostname, new_ip
                ),
            ))
            operations.append((
                "success",
                "A new DNS entry '%s PTR %s' will be created." % (
                    rev, new_hostname
                ),
            ))
            if mac:
                operations.append((
                    "success",
                    "A new DHCP entry '%s %s' will be created." % (
                        new_ip, mac
                    )
                ))
        return operations

    @nested_commit_on_success
    def perform_move(self, address, new_ip, new_hostname):
        old_ipaddress = IPAddress.objects.get(address=address)
        device = old_ipaddress.device
        mac = None
        for r in Record.objects.filter(
                db.Q(name=old_ipaddress.hostname) |
                db.Q(content=old_ipaddress.hostname) |
                db.Q(content=old_ipaddress.address)
        ):
            r.delete()
        for e in DHCPEntry.objects.filter(ip=old_ipaddress.address):
            mac = e.mac
            e.delete()
        old_ipaddress.device = None
        old_ipaddress.save()
        reset_dns(new_hostname, new_ip)
        new_ipaddress, c = IPAddress.concurrent_get_or_create(
            address=new_ip,
        )
        new_ipaddress.device = device
        new_ipaddress.hostname = new_hostname
        new_ipaddress.save()
        if mac:
            entry = DHCPEntry(ip=new_ip, mac=mac)
            entry.save()
        details.device_update_name_rack_dc(device)

    def post(self, *args, **kwargs):
        if 'move' in self.request.POST:
            self.formset = ServerMoveStep3FormSet(
                self.request.POST,
                prefix='step3',
            )
            if self.formset.is_valid():
                for f in self.formset:
                    self.perform_move(
                        f.cleaned_data['address'],
                        f.cleaned_data['new_ip'],
                        f.cleaned_data['new_hostname'],
                    )
                    messages.success(
                        self.request,
                        "Moved %s." % f.cleaned_data['address'],
                    )
                return HttpResponseRedirect(self.request.path)
        elif 'addresses' in self.request.POST:
            self.form = ServerMoveStep1Form(self.request.POST)
            if self.form.is_valid():
                self.formset = ServerMoveStep2FormSet(
                    initial=list(self.step2_initial()),
                    prefix='step2',
                )
                self.form = None
        elif 'step2-TOTAL_FORMS' in self.request.POST:
            self.formset = ServerMoveStep2FormSet(
                self.request.POST,
                prefix='step2',
            )
            self.form = None
            if self.formset.is_valid():
                self.formset = ServerMoveStep3FormSet(
                    initial=list(self.step3_initial()),
                    prefix='step3',
                )
        elif 'step3-TOTAL_FORMS' in self.request.POST:
            self.formset = ServerMoveStep3FormSet(
                self.request.POST,
                prefix='step3',
            )
            if self.formset.is_valid():
                self.operations = self.get_operations(self.formset)
        return self.get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        if self.form is None and self.formset is None:
            self.form = ServerMoveStep1Form()
        ret = super(ServerMove, self).get_context_data(**kwargs)
        ret.update({
            'form': self.form,
            'formset': self.formset,
            'operations': self.operations,
            'details': 'deploy',
            'section': self.kwargs.get('section'),
            'subsection': 'bulk edit',
            'template_selected': 'move_servers',
            'template_menu_items': TEMPLATE_MENU_ITEMS,
        })
        return ret


@nested_commit_on_success
def bulk_update(devices, fields, data, user):
    field_classes = {
        'venture': Venture,
        'venture_role': VentureRole,
        'parent': Device,
    }
    values = {}
    for name in fields:
        if name in field_classes:
            if data[name]:
                values[name] = field_classes[name].objects.get(id=data[name])
            else:
                values[name] = None
        elif name == 'chassis_position' and data[name] == '':
            values[name] = None
        else:
            # for checkboxes un-checking
            values[name] = data.get(name, False)
    if 'service' in fields:
            values['service'] = ServiceCatalog.objects.get(
                id=int(values['service'])
            )
    if 'device_environment' in fields:
        values['device_environment'] = DeviceEnvironment.objects.get(
            id=int(values['device_environment'])
        )
    for device in devices:
        if 'venture' in fields:
            device.venture_role = None
        for name in fields:
            setattr(device, name, values[name])
            device.save_comment = data.get('save_comment')
            device.save(priority=SAVE_PRIORITY, user=user)
            details.device_update_name_rack_dc(device)


class BulkEdit(BaseMixin, TemplateView):
    template_name = 'ui/bulk-edit.html'
    Form = DeviceBulkForm

    def __init__(self, *args, **kwargs):
        super(BulkEdit, self).__init__(*args, **kwargs)
        self.form = None
        self.devices = []
        self.edit_fields = []
        self.different_fields = []

    def post(self, *args, **kwargs):
        profile = self.request.user.get_profile()
        if not profile.has_perm(Perm.bulk_edit):
            messages.error(
                self.request,
                _("You don't have permissions for bulk edit."),
            )
            return super(BulkEdit, self).get(*args, **kwargs)
        selected = self.request.POST.getlist('select')
        devices = Device.objects.filter(id__in=selected).select_related()
        verified = devices.filter(verified=True)
        self.devices = devices.filter(verified=False)
        if not self.devices and not verified:
            messages.error(
                self.request,
                "You haven't selected any existing devices.",
            )
            return HttpResponseRedirect(self.request.path + '../info/')
        elif verified:
            messages.warning(
                self.request,
                "The following devices have been removed from your selection "
                "because they are marked as 'verified' and thus cannot be "
                "edited in bulk: {}. You can either edit them individually "
                "or uncheck the 'verified' option in admin's panel."
                .format(', '.join([d.name for d in verified]))
            )
            if not self.devices:
                return HttpResponseRedirect(self.request.path + '../info/')
        self.edit_fields = self.request.POST.getlist('edit')
        initial = {}
        self.different_fields = []
        for name in self.Form().fields:
            if name == 'save_comment':
                continue
            query = Device.objects.filter(
                id__in=selected
            ).values(name).distinct()
            if query.count() > 1:
                self.different_fields.append(name)
            elif query.count() > 0:
                initial[name] = query[0][name]
        if 'save' in self.request.POST:
            self.form = self.Form(self.request.POST, initial=initial)
            if not self.edit_fields:
                messages.error(self.request, 'Please mark changed fields.')
            elif self.form.is_valid and self.form.data['save_comment']:
                bulk_update(
                    self.devices,
                    self.edit_fields,
                    self.form.data,
                    self.request.user
                )
                messages.success(self.request, 'Changes saved succesfully.')
                return HttpResponseRedirect(self.request.path + '../info/')
            else:
                messages.error(self.request, 'Please correct the errors.')
        elif 'bulk' in self.request.POST:
            self.form = self.Form(initial=initial)
        return super(BulkEdit, self).get(*args, **kwargs)

    def get(self, *args, **kwargs):
        return HttpResponseRedirect(self.request.path + '../info/')

    @property
    def active_submodule(self):
        return self.kwargs.get('section')

    def get_context_data(self, **kwargs):
        ret = super(BulkEdit, self).get_context_data(**kwargs)
        ret.update({
            'form': self.form,
            'details': 'bulkedit',
            'subsection': 'bulk edit',
            'devices': self.devices,
            'edit_fields': self.edit_fields,
            'different_fields': self.different_fields,
        })
        return ret


class Software(DeviceDetailView):
    template_name = 'ui/device_software.html'
    read_perm = Perm.read_device_info_generic

    def get_context_data(self, **kwargs):
        ret = super(Software, self).get_context_data(**kwargs)
        ret.update({'components': _get_details(self.object)})
        return ret


class VhostRedirectView(RedirectView):

    def get_redirect_url(self, **kwargs):
        host = self.request.META.get(
            'HTTP_X_FORWARDED_HOST', self.request.META['HTTP_HOST'])
        user_url = get_user_home_page_url(self.request.user)
        if host == settings.DASHBOARD_SITE_DOMAIN:
            self.url = '/ventures/'
        else:
            self.url = user_url
        return super(VhostRedirectView, self).get_redirect_url(**kwargs)


class Scan(BaseMixin, TemplateView):
    template_name = 'ui/scan.html'
    submodule_name = 'search'

    def get(self, *args, **kwargs):
        try:
            device_id = int(self.kwargs.get('device'))
        except (TypeError, ValueError):
            self.object = None
            try:
                address = IPAddress.objects.get(
                    address=self.kwargs.get('address')
                )
            except IPAddress.DoesNotExist:
                pass
            else:
                if address.device:
                    self.object = address.device
        else:
            self.object = Device.objects.get(id=device_id)
        return super(Scan, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        plugins = self.request.POST.getlist('plugins')
        initial_device_id = self.request.POST.get('initial_device_id')
        if not plugins:
            messages.error(self.request, "You have to select some plugins.")
            return self.get(*args, **kwargs)
        ip_address = (self.kwargs.get('address') or
                      self.request.GET.get('address'))
        if ip_address:
            try:
                ipaddr.IPAddress(ip_address)
            except ValueError:
                # validation reporter by another view, so be silent here.
                return HttpResponseRedirect(reverse('search', args=()))
        try:
            job = queue_scan_address(
                ip_address, plugins, automerge=False, called_from_ui=True
            )
        except ScanError as e:
            messages.error(self.request, unicode(e))
            return self.get(*args, **kwargs)
        url = reverse('scan_results', args=(job.id,))
        if initial_device_id:
            url = url + '?' + urlencode(
                {'initial_device_id': initial_device_id}
            )
        return HttpResponseRedirect(url)

    def get_context_data(self, **kwargs):
        ret = super(Scan, self).get_context_data(**kwargs)
        address = self.kwargs.get('address') or self.request.GET.get('address')
        if address:
            ipaddress, created = IPAddress.objects.get_or_create(address=address)
            try:
                network = Network.from_ip(address)
            except (Network.DoesNotExist, IndexError, ValueError):
                network = None
        else:
            ipaddress = None
            network = None
        if self.object:
            initial_device_id = self.object.id
        elif ipaddress and ipaddress.device_id:
            initial_device_id = ipaddress.device_id
        else:
            initial_device_id = None
        ret.update({
            'details': 'scan',
            'device': self.object,
            'address': address,
            'ipaddress': ipaddress,
            'network': network,
            'plugins': getattr(settings, 'SCAN_PLUGINS', {}),
            'initial_device_id': initial_device_id,
        })
        return ret


class ScanList(BaseMixin, DataTableMixin, TemplateView):
    template_name = 'ui/scan-list.html'
    sort_variable_name = 'sort'
    submodule_name = 'scan_list'

    def __init__(self, *args, **kwargs):
        super(ScanList, self).__init__(*args, **kwargs)
        show_device = (self.column_visible, 'existing')
        show_venture = (self.column_visible, 'existing')
        self.columns = [
            DataTableColumn(
                _('IP'),
                field='ipaddress',
                sort_expression='ipaddress',
                bob_tag=True,
            ),
            DataTableColumn(
                _('Venture'),
                bob_tag=True,
                show_conditions=show_venture,
            ),
            DataTableColumn(
                _('Last scan time'),
                field='modified',
                sort_expression='modified',
                bob_tag=True,
            ),
            DataTableColumn(
                _('Device'),
                bob_tag=True,
                show_conditions=show_device,
            ),
        ]

    def column_visible(self, change_type):
        return self.change_type == change_type

    def get_tab_items(self):
        return []

    def get_context_data(self, **kwargs):
        result = super(ScanList, self).get_context_data(**kwargs)
        result.update(
            super(ScanList, self).get_context_data_paginator(**kwargs)
        )
        changes = get_pending_changes()
        result.update({
            'changed_count': changes.changed_devices if changes else 0,
            'columns': self.columns,
            'new_count': changes.new_devices if changes else 0,
            'change_type': kwargs['change_type'],
            'sort': self.sort,
            'sort_variable_name': self.sort_variable_name,
            'url_query': self.request.GET,
            'venture_service_filter_form': self.form,
        })
        return result

    def get(self, *args, **kwargs):
        self.form = VentureServiceFilterForm(self.request.GET)
        changes = self.handle_search_data(*args, **kwargs)
        self.data_table_query(changes)
        self.change_type = kwargs['change_type']
        return super(ScanList, self).get(*args, **kwargs)

    def handle_search_data(self, *args, **kwargs):
        delta = timezone.now() - datetime.timedelta(seconds=SCAN_RESULT_TTL)
        venture_name = self.request.GET.get('venture')
        service_name = self.request.GET.get('service')
        all_changes = ScanSummary.objects.filter(modified__gt=delta)
        if venture_name or service_name:
            all_changes = all_changes.filter(
                db.Q(ipaddress__device__venture__name=venture_name) |
                db.Q(ipaddress__device__service__name=service_name)
            )
        # see also ralph.scan.util.get_pending_changes (similar condition)
        if kwargs['change_type'] == 'new':
            return all_changes.filter(ipaddress__device=None)
        else:
            return all_changes.filter(ipaddress__device__isnull=False)


class ScanStatus(BaseMixin, TemplateView):
    template_name = 'ui/scan-status.html'
    submodule_name = 'search'

    def __init__(self, *args, **kwargs):
        super(ScanStatus, self).__init__(*args, **kwargs)
        self.forms = []
        self.job = None
        self.device_id = None
        self.ip_address = None

    def set_ip_address(self):
        address = self.kwargs.get('address')
        if not address:
            return
        self.ip_address, created = IPAddress.concurrent_get_or_create(
            address=address,
        )

    def get_job_id_from_address(self):
        self.set_ip_address()
        if self.ip_address and self.ip_address.scan_summary:
            return self.ip_address.scan_summary.job_id

    def get_job(self):
        job_id = self.kwargs.get('job_id')
        if not job_id:
            job_id = self.get_job_id_from_address()
        try:
            return rq.job.Job.fetch(job_id, django_rq.get_connection())
        except rq.exceptions.NoSuchJobError:
            return

    def get_forms(self, result, device_id=None, post=None):
        forms = []
        devices = find_devices(result)
        external_priorities = get_external_results_priorities(result)
        for device in devices:
            device_data = get_device_data(device)
            data = merge_data(
                result,
                {
                    'database': {'device': device_data},
                },
                only_multiple=True,
            )
            append_merged_proposition(data, device, external_priorities)
            sort_results(data)
            diff = diff_results(data)
            if 'ralph_assets' in settings.INSTALLED_APPS:
                if 'asset' not in data and not device_data['asset']:
                    data['asset'] = {
                        (u'database',): device_data['asset'],
                    }
            if post and device.id == device_id:
                form = DiffForm(
                    data, post, default='database', csv_default='merged',
                    diff=diff,
                )
            else:
                form = DiffForm(
                    data, default='database', csv_default='merged',
                    diff=diff,
                )
            forms.append((device, form))
        data = merge_data(result)
        # Add required fields.
        data['model_name'] = data.get('model_name', {})
        data['type'] = data.get('type', {})
        data['mac_addresses'] = data.get('mac_addresses', {})
        data['serial_number'] = data.get('serial_number', {})
        if 'ralph_assets' in settings.INSTALLED_APPS:
            data['asset'] = {}
        if post and device_id == 'new':
            form = DiffForm(data, post, default='custom')
        else:
            form = DiffForm(data, default='custom')
        forms.append((None, form))
        return forms

    def get_context_data(self, **kwargs):
        ret = super(ScanStatus, self).get_context_data(**kwargs)
        if not self.job:
            self.job = self.get_job()
        if not self.job:
            messages.error(
                self.request,
                "This scan has timed out. Please run it again.",
            )
        else:
            plugins = []
            if self.job.args:
                try:
                    self.ip_address = IPAddress.objects.get(
                        address=self.job.args[0],
                    )
                except IPAddress.DoesNotExist:
                    self.set_ip_address()
                if self.job.result is None:
                    plugins = self.job.args[1]
            else:
                self.set_ip_address()
            if self.job.result:
                plugins = self.job.result.keys()
            icons = {
                'success': 'fugue-puzzle',
                'error': 'fugue-cross-button',
                'warning': 'fugue-puzzle--exclamation',
                None: 'fugue-clock',
            }
            bar_styles = {
                'success': 'success',
                'error': 'danger',
                'warning': 'warning',
            }
            ret.update({
                'address': self.ip_address.address,
                'plugins': plugins,
                'status': [
                    (
                        p.split('.')[-1],
                        bar_styles.get(
                            self.job.meta.get('status', {}).get(p),
                        ),
                        icons.get(
                            self.job.meta.get('status', {}).get(p),
                        ),
                    ) for p in plugins
                ],
                'task_size': 100 / len(plugins),
                'scan_summary': self.get_scan_summary(self.job),
                'job': self.job,
            })
            if self.job.is_finished:
                if not self.forms:
                    self.forms = self.get_forms(self.job.result)
                ret['forms'] = self.forms
                if self.device_id is None:
                    device = self.forms[0][0]
                    self.device_id = device.id if device else 'new'
                ret['device_id'] = self.device_id
                ret['initial_device_id'] = self.initial_device_id
        return ret

    def get(self, *args, **kwargs):
        self.initial_device_id = self.request.GET.get('initial_device_id')
        self.job = self.get_job()
        if self.job and self.job.is_finished and not self.ip_address:
            try:
                scan_summary = ScanSummary.objects.get(job_id=self.job.id)
            except ScanSummary.DoesNotExist:
                pass
            else:
                try:
                    self.ip_address = scan_summary.ipaddress_set.all()[0]
                except IndexError:
                    pass
                else:
                    rev_args = (self.ip_address.address,)
                    url = reverse('scan_results', args=rev_args)
                    if self.initial_device_id:
                        url = url + '?' + urlencode(
                            {'initial_device_id': self.initial_device_id}
                        )
                    return HttpResponseRedirect(url)
        return super(ScanStatus, self).get(*args, **kwargs)

    def get_scan_summary(self, job):
        try:
            return ScanSummary.objects.get(job_id=job.id)
        except ScanSummary.DoesNotExist:
            return

    def mark_scan_as_nochanges(self, job):
        scan_summary = self.get_scan_summary(job)
        if scan_summary:
            current_checksum = scan_summary.current_checksum
            scan_summary.false_positive_checksum = current_checksum
            scan_summary.save()

    @transaction.commit_on_success
    def post(self, *args, **kwargs):
        self.device_id = self.request.POST.get('save')
        if self.device_id:
            try:
                self.device_id = int(self.device_id)
            except ValueError:
                pass
        if not self.job:
            self.job = self.get_job()
        if self.job:
            if self.device_id:
                self.forms = self.get_forms(
                    copy.deepcopy(self.job.result),
                    self.device_id,
                    self.request.POST,
                )
                for device, form in self.forms:
                    if form.is_bound:
                        break
                else:
                    form = None
                if form and form.is_valid():
                    data = {
                        field_name: form.get_value(field_name)
                        for field_name in form.result
                    }
                    warnings = []
                    try:
                        if device is None:
                            device = device_from_data(data=data,
                                                      user=self.request.user,
                                                      warnings=warnings)
                        else:
                            set_device_data(device, data, warnings=warnings)
                            device.save(priority=SAVE_PRIORITY,
                                        user=self.request.user)
                        try:
                            selected_type = form.get_value('type')
                        except (KeyError, ValueError):
                            msg = "Wrong or missing device type."
                            raise ValueError(msg)
                        selected_type = get_choice_by_name(DeviceType,
                                                           selected_type)
                        if (selected_type not in ASSET_NOT_REQUIRED and
                                'asset' in form.cleaned_data and
                                form.cleaned_data['asset'] != 'database'):
                            from ralph_assets.api_ralph import assign_asset
                            asset = form.cleaned_data['asset-custom']
                            if not asset:
                                msg = ("Cannot save this type of device "
                                       "without specifying an asset.")
                                raise ValueError(msg)
                            elif not assign_asset(device.id, asset.id):
                                msg = ("Asset id={} cannot be assigned to "
                                       "device id={}."
                                       .format(asset.id, device.id))
                                messages.error(self.request, msg)
                    except ValueError as e:
                        messages.error(self.request, e)
                    else:
                        update_scan_summary(self.job)
                        messages.success(
                            self.request,
                            "Device %s saved." % device,
                        )
                        for warning in warnings:
                            messages.warning(self.request, warning)
                        return HttpResponseRedirect(self.request.path)
                else:
                    messages.error(self.request, "Errors in the form.")
                    for error in form.non_field_errors():
                        messages.error(self.request, error)
            elif self.request.POST.get('no-changes') == 'no-changes':
                self.mark_scan_as_nochanges(self.job)
                messages.success(
                    self.request,
                    "Detected change in this scan was marked as false "
                    "positive.",
                )
                return HttpResponseRedirect(self.request.path)
        return self.get(*args, **kwargs)
