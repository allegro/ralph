#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
from django.template import loader, Context

import ipaddr

from ralph.dnsedit.models import DHCPEntry, DHCPServer
from ralph.discovery.models import Network
from ralph.deployment.models import Deployment
from ralph.dnsedit.util import get_revdns_records


def _get_first_rev(ips):
    for ip in ips:
        for rev in get_revdns_records(ip):
            return rev.content
    return ips[0] if ips else ''


def _generate_networks(networks):
    for network in networks.exclude(dhcp_config=''):
        net = ipaddr.IPNetwork(network.address)
        yield (
            network.name,
            str(net.network),
            str(net.netmask),
            network.dhcp_config,
        )


def _generate_entries(filter_ips, dc):
    for macaddr, in DHCPEntry.objects.values_list('mac').distinct():
        ips = list(filter_ips(
            ip for (ip,) in
            DHCPEntry.objects.filter(mac=macaddr).values_list('ip')
        ))
        if not ips:
            continue
        if Deployment.objects.filter(mac=macaddr).exists():
            data_center = dc
            if not data_center:
                for net in Network.all_from_ip(ips[0]):
                    data_center = net.data_center
                    if data_center:
                        break
            if data_center:
                next_server = data_center.next_server
        else:
            next_server = ''
        name = _get_first_rev(ips)
        address = ', '.join(ips)
        mac = ':'.join('%s%s' % c for c in zip(macaddr[::2],
                                                macaddr[1::2])).upper()
        yield name, address, mac, next_server


def generate_dhcp_config(dc=None, server_address=None, with_networks=False):
    """Generate host DHCP configuration. If `dc` is provided, only yield hosts
    with addresses from networks of the specified DC.

    If given, `dc` must be of type DataCenter.
    """
    server = None
    if server_address:
        try:
            server = DHCPServer.objects.get(ip=server_address)
        except DHCPServer.DoesNotExist:
            pass
    template = loader.get_template('dnsedit/dhcp.conf')
    last_modified_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for last in DHCPEntry.objects.order_by('-modified')[:1]:
        last_modified_date = last.modified.strftime('%Y-%m-%d %H:%M:%S')
        break
    if dc:
        networks = dc.network_set.all()
        nets = {ipaddr.IPNetwork(network.address) for network in networks}
        def filter_ips(ips):
            for ip in ips:
                ip_address = ipaddr.IPAddress(ip)
                for net in nets:
                    if ip_address in net:
                        yield ip
                        break
    else:
        networks = Network.objects.all()
        def filter_ips(ips):
            return ips
    for last in networks.exclude(dhcp_config='').order_by('-modified')[:1]:
        last_modified_date = max(
            last_modified_date,
            last.modified.strftime('%Y-%m-%d %H:%M:%S'),
        )
        break
    c = Context({
        'server_config': server.dhcp_config if server else '',
        'networks': _generate_networks(networks) if with_networks else [],
        'entries': _generate_entries(filter_ips, dc),
        'last_modified_date': last_modified_date,
    })
    return template.render(c)

