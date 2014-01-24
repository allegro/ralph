# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

import django_rq
import rq

from bob.menu import MenuItem
from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils import timezone


from ralph.account.models import Perm
from ralph.discovery.models import ReadOnlyDevice, Network, IPAddress
from ralph.ui.forms import NetworksFilterForm
from ralph.ui.forms.network import NetworkForm
from ralph.ui.views.common import (
    Addresses,
    Asset,
    BaseMixin,
    Components,
    Costs,
    Info,
    History,
    Prices,
    Software,
    Scan,
)
from ralph.ui.views.devices import BaseDeviceList
from ralph.ui.views.reports import Reports, ReportDeviceList
from ralph.util import presentation
from ralph.scan import autoscan


def network_tree_menu(networks, details, show_ip=False, status=''):
    icon = presentation.get_network_icon
    items = []
    for n in networks:
        items.append(MenuItem(
            "{} ({})".format(
                n['network'].name, n['network'].address,
            ),
            fugue_icon=icon(n['network']),
            view_name='networks',
            indent='  ',
            name=n['network'].name,
            view_args=[n['network'].name, details, status],
            subitems=network_tree_menu(
                n['subnetworks'], details, show_ip, status,
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
        network_symbol = self.kwargs.get('network')
        if network_symbol == '-':
            self.network = ''
        elif network_symbol:
            self.network = get_object_or_404(Network,
                                             name__iexact=network_symbol)
        else:
            self.network = None

    def get_context_data(self, **kwargs):
        ret = super(SidebarNetworks, self).get_context_data(**kwargs)
        profile = self.request.user.get_profile()
        has_perm = profile.has_perm
        self.set_network()
        networks = Network.objects.all()
        contains = self.request.GET.get('contains')
        if contains:
            networks = networks.filter(
                Q(name__contains=contains) | Q(address__contains=contains)
            )
        self.networks = Network.prepare_network_tree(qs=networks)
        sidebar_items = [
            MenuItem(fugue_icon='fugue-prohibition',
                     label="None", name='',
                     view_name='networks',
                     view_args=['-', ret['details'], self.status]),
        ]
        sidebar_items.extend(
            network_tree_menu(
                self.networks,
                ret['details'],
                show_ip=self.request.GET.get('show_ip'),
                status=self.status,
            ),
        )
        if has_perm(Perm.edit_device_info_generic) and not self.object:
            ret['tab_items'].extend([
                MenuItem('Autoscan', fugue_icon='fugue-radar',
                         href=self.tab_href('autoscan', 'new')),
            ])

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


class Networks(SidebarNetworks, BaseMixin):
    def get_context_data(self, **kwargs):
        ret = super(BaseMixin, self).get_context_data(**kwargs)
        tab_menu = [
            MenuItem('Info', fugue_icon='fugue-wooden-box',
                     href=self.tab_href('info')),
        ]
        show_tabs = [
            'info',
        ]
        context = {
            'show_tabs': show_tabs,
            'tab_items': tab_menu,
        }
        ret.update(context)
        return ret


class NetworksDeviceList(SidebarNetworks, BaseMixin, BaseDeviceList):

    def user_allowed(self):
        has_perm = self.request.user.get_profile().has_perm
        return has_perm(Perm.read_network_structure)

    def get_queryset(self):
        self.set_network()
        if self.network is None:
            return ReadOnlyDevice.objects.none()
        if self.network == '':
            return ReadOnlyDevice.objects.filter(
                ipaddress=None
            ).order_by(
                'dc', 'rack', 'model__type', 'position'
            )
        addresses = IPAddress.objects.filter(
                number__gte=self.network.min_ip,
                number__lte=self.network.max_ip,
            )
        queryset = ReadOnlyDevice.objects.filter(
                ipaddress__in=addresses
            ).order_by(
                'dc', 'rack', 'model__type', 'position'
            )
        return super(NetworksDeviceList, self).get_queryset(queryset)

    def get_context_data(self, **kwargs):
        ret = super(NetworksDeviceList, self).get_context_data(**kwargs)
        ret.update({
            'subsection': self.network.name if self.network else self.network,
        })
        return ret


class NetworksInfo(Networks, Info):
    pass


class NetworksComponents(Networks, Components):
    pass


class NetworksSoftware(Networks, Software):
    pass


class NetworksPrices(Networks, Prices):
    pass


class NetworksAddresses(Networks, Addresses):
    pass


class NetworksCosts(Networks, Costs):
    pass


class NetworksHistory(Networks, History):
    pass


class NetworksAsset(Networks, Asset):
    pass


class NetworksReports(Networks, Reports):
    pass


class NetworksScan(Networks, Scan):
    pass


class ReportNetworksDeviceList(ReportDeviceList, NetworksDeviceList):
    pass


class NetworksAutoscan(SidebarNetworks, BaseMixin, BaseDeviceList):
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
        })
        return ret

    def post(self, *args, **kwargs):
        self.set_network()
        if 'scan' in self.request.POST and self.network:
            autoscan.autoscan_network(self.network)
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
