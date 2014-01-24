#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

import ipaddr

from django.template import loader, Context
from django.db.models import Q
from powerdns.models import Record

from ralph.dnsedit.models import DHCPEntry, DHCPServer, DNSServer
from ralph.discovery.models import Network, Ethernet, IPAddress
from ralph.deployment.models import Deployment


def _generate_entries_configs(
    dc=None,
    possible_ip_numbers=set(),
    ptr_records={},
    deployed_macs=set(),
):
    parsed = set()
    for ip_address, mac, ip_number in DHCPEntry.objects.values_list(
        'ip', 'mac', 'number',
    ):
        if any((
            ip_number not in possible_ip_numbers,
            ip_address in parsed,
        )):
            continue
        ptr_name = '.'.join(reversed(ip_address.split('.'))) + '.in-addr.arpa'
        name = ptr_records.get(ptr_name)
        if name is None:
            try:
                eth = Ethernet.objects.get(mac=mac)
            except Ethernet.DoesNotExist:
                continue
            else:
                try:
                    name = IPAddress.objects.get(
                        number=ip_number,
                        device_id=eth.device.id,
                    ).hostname
                except IPAddress.DoesNotExist:
                    continue
                else:
                    if not name:
                        # hostname could be empty, so skip it...
                        continue
        next_server = ''
        if mac in deployed_macs:
            # server with ePXE image address
            if dc and dc.next_server:
                next_server = dc.next_server
            else:
                for dc_next_server in Network.objects.filter(
                    min_ip__lte=ip_number,
                    max_ip__gte=ip_number,
                    data_center__isnull=False,
                ).values_list(
                    'data_center__next_server',
                    flat=True,
                ).order_by('-min_ip', 'max_ip'):
                    if dc_next_server:
                        next_server = dc_next_server
                        break
        parsed.add(ip_address)
        # 112233445566 -> 11:22:33:44:55:66
        mac = ':'.join('%s%s' % chunk for chunk in zip(mac[::2], mac[1::2]))
        yield name.strip(), ip_address, mac, next_server


def generate_dhcp_config(server_address, dc=None):
    """
    Generate host DHCP configuration. If `dc` is provided, only yield hosts
    with addresses from networks of the specified DC.

    If given, `dc` must be of type DataCenter.
    """

    try:
        dhcp_server = DHCPServer.objects.get(ip=server_address)
    except DHCPServer.DoesNotExist:
        dhcp_server = None
        last_modified_date = datetime.datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S',
        )
    else:
        last_modified_date = dhcp_server.modified.strftime('%Y-%m-%d %H:%M:%S')
    networks_filter = (
        Q(dhcp_broadcast=True),
        Q(gateway__isnull=False),
        ~Q(gateway__exact=''),
        ~Q(data_center=False),
        Q(data_center__domain__isnull=False),
        ~Q(data_center__domain__exact=''),
    )
    if dc:
        networks = dc.network_set.filter(*networks_filter)
    else:
        networks = Network.objects.filter(*networks_filter)
    for modified in networks.values_list(
        'modified', flat=True,
    ).order_by('-modified')[:1]:
        if dhcp_server:
            last_modified_date = max(
                last_modified_date,
                modified.strftime('%Y-%m-%d %H:%M:%S'),
            )
        else:
            last_modified_date = modified.strftime('%Y-%m-%d %H:%M:%S')
        break
    possible_ip_numbers = set()
    for min_ip, max_ip in networks.values_list('min_ip', 'max_ip'):
        for ip_number in xrange(min_ip, max_ip + 1):
            possible_ip_numbers.add(ip_number)
    ptr_records = {}
    for name, content in Record.objects.filter(type='PTR').values_list(
        'name', 'content',
    ):
        ptr_records[name] = content
    deployed_macs = Deployment.objects.values_list('mac', flat=True)
    for modified in DHCPEntry.objects.values_list(
        'modified',
        flat=True,
    ).order_by('-modified')[:1]:
        last_modified_date = max(
            last_modified_date,
            modified.strftime('%Y-%m-%d %H:%M:%S'),
        )
        break
    template = loader.get_template('dnsedit/dhcp.conf')
    c = Context({
        'entries': _generate_entries_configs(
            dc=dc,
            possible_ip_numbers=possible_ip_numbers,
            ptr_records=ptr_records,
            deployed_macs=deployed_macs,
        ),
        'last_modified_date': last_modified_date,
    })
    return template.render(c)


def _generate_networks_configs(networks, custom_dns_servers):
    for network_id, name, address, gateway, domain, dhcp_config in networks:
        ip_network = ipaddr.IPNetwork(address)
        yield (
            name.strip(),
            unicode(ip_network.network),
            unicode(ip_network.netmask),
            gateway,
            domain,
            dhcp_config,
            ','.join(
                custom_dns_servers[network_id],
            ) if network_id in custom_dns_servers else '',
        )


def generate_dhcp_config_head(server_address, dc=None):
    try:
        dhcp_server = DHCPServer.objects.get(ip=server_address)
    except DHCPServer.DoesNotExist:
        dhcp_server = None
        last_modified_date = datetime.datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S',
        )
        dhcp_server_config = None
    else:
        last_modified_date = dhcp_server.modified.strftime('%Y-%m-%d %H:%M:%S')
        dhcp_server_config = dhcp_server.dhcp_config
    networks_filter = (
        Q(dhcp_broadcast=True),
        Q(gateway__isnull=False),
        ~Q(gateway__exact=''),
        ~Q(data_center=False),
        Q(data_center__domain__isnull=False),
        ~Q(data_center__domain__exact=''),
    )
    if dc:
        networks = dc.network_set.filter(*networks_filter)
    else:
        networks = Network.objects.filter(*networks_filter)
    for modified in networks.values_list(
        'modified', flat=True,
    ).order_by('-modified')[:1]:
        if dhcp_server:
            last_modified_date = max(
                last_modified_date,
                modified.strftime('%Y-%m-%d %H:%M:%S'),
            )
        else:
            last_modified_date = modified.strftime('%Y-%m-%d %H:%M:%S')
        break
    networks = networks.values_list(
        'id',
        'name',
        'address',
        'gateway',
        'data_center__domain',
        'dhcp_config',
    ).order_by('name')
    for modified in DHCPEntry.objects.values_list(
        'modified', flat=True,
    ).order_by('-modified')[:1]:
        last_modified_date = max(
            last_modified_date,
            modified.strftime('%Y-%m-%d %H:%M:%S'),
        )
        break
    template = loader.get_template('dnsedit/dhcp_head.conf')
    default_dns_servers = DNSServer.objects.filter(
        is_default=True,
    ).values_list('ip_address', flat=True).order_by('id')
    # make some usefull cache...
    custom_dns_servers = {}
    for dns_server_ip, network_id in DNSServer.objects.values_list(
        'ip_address', 'network__id',
    ):
        if not network_id:
            continue
        if network_id not in custom_dns_servers:
            custom_dns_servers[network_id] = set()
        custom_dns_servers[network_id].add(dns_server_ip)
    context = Context({
        'dhcp_server_config': dhcp_server_config,
        'dns_servers': ','.join(default_dns_servers),
        'networks': _generate_networks_configs(networks, custom_dns_servers),
        'last_modified_date': last_modified_date,
    })
    return template.render(context)

