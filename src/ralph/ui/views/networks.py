# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import urllib

import django_rq
import rq

from bob.menu import MenuItem
from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.core.urlresolvers import reverse
from django.views.generic import (
    UpdateView,
    TemplateView,
)

from ralph.account.models import Perm
from ralph.discovery.models import Network, IPAddress
from ralph.ui.forms.network import NetworkForm, NetworksFilterForm
from ralph.ui.views.common import (
    Asset,
    BaseMixin,
    Components,
    Costs,
    History,
    Prices,
    Software,
    Scan,
)
from ralph.ui.views.devices import BaseDeviceList
from ralph.ui.views.reports import Reports, ReportDeviceList
from ralph.util import presentation
from ralph.scan import autoscan
from ralph.deployment.util import get_first_free_ip
from ralph.discovery.models_network import get_network_tree


from django.core.cache import cache


def network_tree_menu(networks, details, get_params, show_ip=False, status=''):
    icon = presentation.get_network_icon
    items = []

    def get_href(view_args):
        view_args = map(
            lambda arg: urllib.quote(arg.encode('utf-8'), ''),
            view_args,
        )
        url = reverse("networks", args=view_args)
        return '%s?%s' % (
            url,
            get_params,
        )
    for n in networks:
        items.append(MenuItem(
            "{} ({})".format(n['network'].name, n['network'].address,),
            fugue_icon=icon(n['network']),
            view_name='networks',
            indent='  ',
            href=get_href(view_args=[str(n['network'].id), details, status]),
            name=n['network'].name,
            subitems=network_tree_menu(
                n['subnetworks'], details, get_params, show_ip, status,
            ),
            collapsible=True,
            collapsed=not getattr(n['network'], 'expanded', False),
        ))
    return items


class SidebarNetworks(object):
    section = 'networks'

    def __init__(self, *args, **kwargs):
        super(SidebarNetworks, self).__init__(*args, **kwargs)
        self.network = None
        self.status = ''

    def set_network(self):
        if self.network:
            return self.network
        network_id = self.kwargs.get('network_id')
        if network_id:
            self.network = get_object_or_404(Network, id=network_id)
        else:
            self.network = None
        return self.network

    def get_context_data(self, **kwargs):
        ret = super(SidebarNetworks, self).get_context_data(**kwargs)
        self.set_network()
        networks = Network.objects.all().select_related("kind__icon")
        contains = self.request.GET.get('contains')
        if contains:
            networks_filtered = Network.objects.filter(
                Q(name__contains=contains) | Q(address__contains=contains)
            )
            minimax = [(n.min_ip, n.max_ip) for n in networks_filtered]
            ids = []
            for mini, maxi in minimax:
                ids.extend(
                    map(
                        lambda net: net['id'],
                        Network.objects.filter(
                            min_ip__gte=mini,
                            max_ip__lte=maxi,
                        ).values('id')
                    )
                )
            networks = networks.filter(id__in=ids)
        network_kind = self.request.GET.get('kind')
        if network_kind:
            networks = networks.filter(
                kind__id=int(network_kind),
            )
        networks = networks.order_by('-min_ip', 'max_ip')

        sidebar_items = cache.get('cache_network_sidebar_items')
        if not sidebar_items:
            self.networks = get_network_tree(
                qs=networks
            )
            sidebar_items = []
            sidebar_items.extend(
                network_tree_menu(
                    self.networks,
                    ret['details'],
                    status=self.status,
                    get_params=self.request.GET.urlencode(),
                ),
            )
            # indef.
            cache.set('cache_network_sidebar_items', sidebar_items, None)

        ret.update({
            'sidebar_items': sidebar_items,
            'sidebar_selected': (self.network.name if
                                 self.network else self.network),
            'section': 'networks',
            'subsection': self.network.name if self.network else self.network,
            'searchform': NetworksFilterForm(self.request.GET),
            'searchform_filter': True,
            'sidebar_alternative_span': 'span3',
            'content_alternative_span': 'span9',
        })
        return ret


class NetworksMixin(SidebarNetworks, BaseMixin):

    def tab_href(self, name, obj=''):
        args = [self.kwargs.get('network_id'), name]
        if obj:
            args.append(obj)
        return '%s?%s' % (
            reverse("networks", args=args),
            self.request.GET.urlencode(),
        )

    def get_tab_items(self):
        return []

    def get_context_data(self, **kwargs):
        ret = super(NetworksMixin, self).get_context_data(**kwargs)
        tab_menu = [
            MenuItem('Info', fugue_icon='fugue-wooden-box',
                     href=self.tab_href('info')),
            MenuItem('Addresses', fugue_icon='fugue-network-ip',
                     href=self.tab_href('addresses')),
            MenuItem('Autoscan', fugue_icon='fugue-radar',
                     href=self.tab_href('autoscan')),
        ]
        show_tabs = [
            'info',
            'addresses',
            'autoscan',
        ]
        context = {
            'show_tabs': show_tabs,
            'tab_items': tab_menu,
        }
        context['network'] = self.set_network()
        ret.update(context)
        return ret


class NetworksDeviceList(NetworksMixin, TemplateView):
    template_name = "ui/network_list.html"

    def user_allowed(self):
        has_perm = self.request.user.get_profile().has_perm
        return has_perm(Perm.read_network_structure)


class NetworksInfo(NetworksMixin, UpdateView):
    model = Network
    slug_field = 'name'
    slug_url_kwarg = 'network'
    template_name = 'ui/network_info.html'
    form_class = NetworkForm

    def get_property_form(self):
        return None

    def get_context_data(self, **kwargs):
        ret = super(NetworksInfo, self).get_context_data(**kwargs)
        next_free_ip = get_first_free_ip(self.network.name)
        ret['next_free_ip'] = next_free_ip
        ret['editable'] = True
        for error in ret['form'].non_field_errors():
            messages.error(self.request, error)
        return ret

    def get_object(self):
        self.set_network()
        return self.network


class NetworksComponents(NetworksMixin, Components):
    pass


class NetworksSoftware(NetworksMixin, Software):
    pass


class NetworksPrices(NetworksMixin, Prices):
    pass


class NetworksAddresses(NetworksMixin, TemplateView):
    template_name = "ui/network_addresses.html"

    def get_context_data(self, **kwargs):
        ret = super(NetworksAddresses, self).get_context_data(**kwargs)
        aggregated = self.network.get_ip_usage_aggegated()
        ret['ip_usage'] = aggregated
        return ret


class NetworksCosts(NetworksMixin, Costs):
    pass


class NetworksHistory(NetworksMixin, History):
    pass


class NetworksAsset(NetworksMixin, Asset):
    pass


class NetworksReports(NetworksMixin, Reports):
    pass


class NetworksScan(NetworksMixin, Scan):
    template_name = 'ui/scan_networks.html'


class ReportNetworksDeviceList(ReportDeviceList, NetworksDeviceList):
    pass


class NetworksAutoscan(NetworksMixin, BaseDeviceList):
    template_name = 'ui/address_list.html'
    section = 'networks'

    def user_allowed(self):
        profile = self.request.user.get_profile()
        return profile.has_perm(Perm.edit_device_info_generic)

    def get_queryset(self):
        self.status = self.kwargs.get('status', 'new') or 'new'
        self.set_network()
        if self.network is None:
            query = IPAddress.objects.none()
        if self.network == '':
            query = IPAddress.objects.all()
        else:
            query = self.network.ipaddress_set.all()
        if self.status == 'new':
            query = query.filter(
                dead_ping_count=0,
            ).exclude(
                device__deleted=False,
            ).exclude(
                device__isnull=False,
            )
            query = query.filter(is_buried=False)
        elif self.status == 'changed':
            query = query.filter(is_buried=False)
        elif self.status == 'dead':
            query = query.filter(
                dead_ping_count__gt=settings.DEAD_PING_COUNT,
                device__isnull=False,
            ).exclude(
                device__deleted=True,
            )
            query = query.filter(is_buried=False)
        elif self.status == 'buried':
            query = query.filter(is_buried=True)
        elif self.status == 'all':
            query = query.all()
        else:
            query = IPAddress.objects.none()
        return self.sort_queryset(
            query,
            columns={
                'address': ('number',),
                'hostname': ('hostname',),
                'last_seen': ('last_seen',),
                'device': ('device__model__name',),
                'snmp_name': ('snmp_name',),
                'http_family': ('http_family'),
            },
        )

    def append_scan_summary_info(self, ip_addresses):
        if not ip_addresses:
            return
        delta = timezone.now() - datetime.timedelta(days=1)
        for ip_address in ip_addresses:
            if (
                ip_address.scan_summary and
                ip_address.scan_summary.modified > delta
            ):
                try:
                    job = rq.job.Job.fetch(
                        ip_address.scan_summary.job_id,
                        django_rq.get_connection(),
                    )
                except rq.exceptions.NoSuchJobError:
                    continue
                else:
                    ip_address.scan_summary.changed = job.meta.get(
                        'changed',
                        False,
                    )

    def get_context_data(self, **kwargs):
        ret = super(NetworksAutoscan, self).get_context_data(**kwargs)
        status_menu_items = [
            MenuItem(
                'New',
                fugue_icon='fugue-star',
                href=self.tab_href('autoscan', 'new'),
            ),
            MenuItem(
                'Changed',
                fugue_icon='fugue-question',
                href=self.tab_href('autoscan', 'changed'),
            ),
            MenuItem(
                'Dead',
                fugue_icon='fugue-skull',
                href=self.tab_href('autoscan', 'dead'),
            ),
            MenuItem(
                'Buried',
                fugue_icon='fugue-headstone',
                href=self.tab_href('autoscan', 'buried'),
            ),
            MenuItem(
                'All',
                fugue_icon='fugue-network-ip',
                href=self.tab_href('autoscan', 'all'),
            ),
        ]
        self.append_scan_summary_info(ret['object_list'])
        ret.update({
            'status_menu_items': status_menu_items,
            'status_selected': self.status,
            'network': self.network,
            'details': 'autoscan',
            'network_name': self.network.name if self.network else '-',
            'network_id': self.network.id,
        })
        return ret

    def post(self, *args, **kwargs):
        self.set_network()
        if 'scan' in self.request.POST and self.network:
            autoscan.queue_autoscan_network(self.network)
            messages.success(self.request, "Network scan scheduled.")
        elif 'bury' in self.request.POST:
            selected = self.request.POST.getlist('select')
            addresses = IPAddress.objects.filter(id__in=selected)
            for address in addresses:
                address.is_buried = True
                address.save(update_last_seen=False)
            messages.success(
                self.request,
                "%d addresses buried." % len(addresses),
            )
        elif 'resurrect' in self.request.POST:
            selected = self.request.POST.getlist('select')
            addresses = IPAddress.objects.filter(id__in=selected)
            for address in addresses:
                address.is_buried = False
                address.save(update_last_seen=False)
            messages.success(
                self.request,
                "%d addresses resurrected." % len(addresses),
            )
        return HttpResponseRedirect(self.request.path)
