# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import collections

from bob.menu import MenuItem
from django.db.models import Q
from django.shortcuts import get_object_or_404

from ralph.account.models import Perm
from ralph.discovery.models import ReadOnlyDevice, Network, IPAddress
from ralph.ui.forms import NetworksFilterForm
from ralph.ui.views.common import (BaseMixin, DeviceDetailView, CMDB, Info,
                                   Prices, Addresses, Costs, Purchase,
                                   Components, History, Discover)
from ralph.ui.views.devices import BaseDeviceList
from ralph.ui.views.reports import Reports, ReportDeviceList
from ralph.util import presentation


def network_tree_menu(networks, details, children, show_ip):
    icon = presentation.get_network_icon
    items = []
    for n in networks:
        items.append(MenuItem(
            n.address if show_ip else n.name,
            fugue_icon=icon(n),
            view_name='networks',
            indent=' ',
            name=n.name,
            view_args=[n.name, details, ''],
            subitems = network_tree_menu(children[n.id], details, children, show_ip),
            collapsible=True,
            collapsed=not getattr(n, 'expanded', False),
        ))
    return items


class SidebarNetworks(object):
    def __init__(self, *args, **kwargs):
        super(SidebarNetworks, self).__init__(*args, **kwargs)
        self.network = None

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
        self.set_network()
        networks = Network.objects.all()
        contains =  self.request.GET.get('contains')
        if contains:
            networks = networks.filter(
                    Q(name__contains=contains) |
                    Q(address__contains=contains)
                )
        self.networks = list(networks.order_by('min_ip', 'max_ip'))
        stack = []
        children = collections.defaultdict(list)
        for network in self.networks:
            network.parent = None
            while stack:
                if network in stack[-1]:
                    network.parent = stack[-1]
                    children[stack[-1].id].append(network)
                    break
                else:
                    stack.pop()
            if network.parent:
                network.depth = network.parent.depth + 1
            else:
                network.depth = 0
            network.indent = ' ' * network.depth
            stack.append(network)
            if network == self.network:
                parent = getattr(network, 'parent', None)
                while parent:
                    parent.expanded = True
                    parent = getattr(parent, 'parent', None)
        sidebar_items = [MenuItem(fugue_icon='fugue-prohibition',
                                  label="None", name='',
                                  view_name='networks',
                                  view_args=['-', ret['details'],''])]
        sidebar_items.extend(network_tree_menu(
            [n for n in self.networks if n.parent is None],
            ret['details'], children, show_ip=self.request.GET.get('show_ip')))
        ret.update({
            'sidebar_items': sidebar_items,
            'sidebar_selected': (self.network.name if
                                 self.network else self.network),
            'section': 'networks',
            'subsection': self.network.name if self.network else self.network,
            'searchform': NetworksFilterForm(self.request.GET),
            'searchform_filter': True,
        })
        return ret


class Networks(SidebarNetworks, BaseMixin):
    pass


class NetworksDeviceList(SidebarNetworks, BaseMixin, BaseDeviceList):
    section = 'networks'

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


class NetworksPrices(Networks, Prices):
    pass


class NetworksAddresses(Networks, Addresses):
    pass


class NetworksCosts(Networks, Costs):
    pass


class NetworksHistory(Networks, History):
    pass


class NetworksPurchase(Networks, Purchase):
    pass


class NetworksDiscover(Networks, Discover):
    pass


class NetworksCMDB(Networks, CMDB, DeviceDetailView):
    pass


class NetworksReports(Networks, Reports):
    pass


class ReportNetworksDeviceList(ReportDeviceList, NetworksDeviceList):
    pass

