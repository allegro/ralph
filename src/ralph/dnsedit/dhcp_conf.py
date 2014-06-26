#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import ipaddr
import logging

from django.template import loader, Context
from django.db.models import Q
from powerdns.models import Record

from ralph.dnsedit.models import DHCPEntry, DNSServer
from ralph.discovery.models import Network, Ethernet, IPAddress, Environment
from ralph.deployment.models import Deployment


logger = logging.getLogger("DHCP")


def _generate_entries_configs(
    possible_ip_numbers=set(),
    ptr_records={},
    deployed_macs=set(),
    accept_all_ip_numbers=False,
):
    parsed = set()
    used_names = set()
    for ip_address, mac, ip_number in DHCPEntry.objects.values_list(
        'ip', 'mac', 'number',
    ):
        if any((
            not accept_all_ip_numbers and
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
                logger.warning(
                    'MAC: {}; No PTR record found; No connected device '
                    'found.'.format(
                        mac
                    ),
                )
                continue
            else:
                try:
                    name = IPAddress.objects.get(
                        number=ip_number,
                        device_id=eth.device.id,
                    ).hostname
                except IPAddress.DoesNotExist:
                    logger.warning(
                        'MAC: {}; No PTR record found; No connected IP '
                        'address found. [DeviceID: {}]'.format(
                            mac, eth.device.id,
                        ),
                    )
                    continue
                else:
                    if not name:
                        # hostname could be empty, so skip it...
                        logger.warning(
                            'MAC: {}; No PTR record found; Connected IP '
                            'address has empty hostname. '
                            '[IPAddress: {} DeviceID: {}]'.format(
                                mac,
                                unicode(ipaddr.IPAddress(ip_number)),
                                eth.device.id,
                            ),
                        )
                        continue
        if name in used_names:
            logger.warning(
                'MAC: {}; Found multiple domain {} occurrence in config. '
                '[IPAddress: {}]'.format(
                    mac,
                    name,
                    ip_address
                )
            )
            continue
        used_names.add(name)
        next_server = ''
        if mac in deployed_macs:
            # server with ePXE image address
            for env_next_server in Network.objects.filter(
                min_ip__lte=ip_number,
                max_ip__gte=ip_number,
                environment__isnull=False,
            ).values_list(
                'environment__next_server',
                flat=True,
            ).order_by('-min_ip', 'max_ip'):
                if env_next_server:
                    next_server = env_next_server
                    break
        parsed.add(ip_address)
        # 112233445566 -> 11:22:33:44:55:66
        mac = ':'.join('%s%s' % chunk for chunk in zip(mac[::2], mac[1::2]))
        yield name.strip(), ip_address, mac, next_server


def generate_dhcp_config_entries(
    data_centers=[], environments=[], disable_networks_validation=False,
):
    """
    Generate host DHCP configuration. If `env` is provided, only yield hosts
    with addresses from networks of the specified environment.

    If given, `env` must be of type Environment.
    """
    last_modified_date = None
    if disable_networks_validation:
        networks_filter = tuple()
    else:
        networks_filter = (
            Q(dhcp_broadcast=True),
            Q(gateway__isnull=False),
            ~Q(gateway__exact=''),
        )
    if environments:
        networks_filter += (
            ~Q(environment=False),
        )
        if not disable_networks_validation:
            networks_filter += (
                Q(environment__domain__isnull=False),
                ~Q(environment__domain__exact=''),
            )
        networks = Network.objects.filter(
            environment__in=environments,
            *networks_filter
        )
    elif data_centers:
        if not disable_networks_validation:
            evironments_filter = (
                Q(domain__isnull=False),
                ~Q(domain__exact=''),
            )
        else:
            evironments_filter = tuple()
        environments_ids = Environment.objects.filter(
            data_center__in=data_centers,
            *evironments_filter
        ).values_list('id', flat=True)
        networks_filter += (
            Q(environment_id__in=environments_ids),
        )
        networks = Network.objects.filter(*networks_filter)
    else:
        networks = Network.objects.filter(*networks_filter)
    for modified in networks.values_list(
        'modified', flat=True,
    ).order_by('-modified')[:1]:
        last_modified_date = modified.strftime('%Y-%m-%d %H:%M:%S')
        break
    possible_ip_numbers = set()
    if data_centers or environments or not disable_networks_validation:
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
    template = loader.get_template('dnsedit/dhcp_entries.conf')
    accept_all_ip_numbers = (
        not data_centers and not environments and disable_networks_validation
    )
    if last_modified_date is None:
        last_modified_date = '???'
    c = Context({
        'entries': _generate_entries_configs(
            possible_ip_numbers=possible_ip_numbers,
            ptr_records=ptr_records,
            deployed_macs=deployed_macs,
            accept_all_ip_numbers=accept_all_ip_numbers,
        ),
        'last_modified_date': last_modified_date
    })
    return template.render(c)


def _generate_networks_configs(
    networks, custom_dns_servers, default_dns_servers=[]
):
    for network_id, name, address, gateway, domain, dhcp_config in networks:
        ip_network = ipaddr.IPNetwork(address)
        dns_servers = ','.join(
            custom_dns_servers[network_id],
        ) if network_id in custom_dns_servers else ''
        if not dns_servers and not default_dns_servers:
            continue
        yield (
            name.strip(),
            unicode(ip_network.network),
            unicode(ip_network.netmask),
            gateway,
            domain,
            dhcp_config,
            dns_servers,
        )


def generate_dhcp_config_networks(data_centers=[], environments=[]):
    last_modified_date = None
    networks_filter = (
        Q(dhcp_broadcast=True),
        Q(gateway__isnull=False),
        ~Q(gateway__exact=''),
        ~Q(environment=False),
        Q(environment__domain__isnull=False),
        ~Q(environment__domain__exact=''),
    )
    if environments:
        networks = Network.objects.filter(
            environment__in=environments, *networks_filter
        )
    elif data_centers:
        environments_ids = Environment.objects.filter(
            data_center__in=data_centers
        ).values_list('id', flat=True)
        networks_filter += (
            Q(environment_id__in=environments_ids),
        )
        networks = Network.objects.filter(*networks_filter)
    else:
        networks = Network.objects.filter(*networks_filter)
    for modified in networks.values_list(
        'modified', flat=True,
    ).order_by('-modified')[:1]:
        last_modified_date = modified.strftime('%Y-%m-%d %H:%M:%S')
        break
    networks = networks.values_list(
        'id',
        'name',
        'address',
        'gateway',
        'environment__domain',
        'dhcp_config',
    ).order_by('name')
    template = loader.get_template('dnsedit/dhcp_networks.conf')
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
    if last_modified_date is None:
        last_modified_date = '???'
    context = Context({
        'dns_servers': ','.join(default_dns_servers),
        'networks': _generate_networks_configs(
            networks, custom_dns_servers, default_dns_servers
        ),
        'last_modified_date': last_modified_date,
    })
    return template.render(context)


def generate_dhcp_config_head(dhcp_server):
    template = loader.get_template('dnsedit/dhcp_head.conf')
    context = Context({
        'dhcp_server_config': dhcp_server.dhcp_config,
        'last_modified_date': dhcp_server.modified.strftime(
            '%Y-%m-%d %H:%M:%S',
        ),
    })
    return template.render(context)
