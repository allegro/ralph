# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from django.db.models import Q
import ipaddr
from lck.django.common.models import MACAddressField
from lck.django.common import nested_commit_on_success
from powerdns.models import Record

from ralph.business.models import VentureRole
from ralph.deployment.models import Preboot, Deployment, DeploymentStatus
from ralph.discovery.models import (
    Device,
    DeviceType,
    Ethernet,
    EthernetSpeed,
    IPAddress,
    Network,
)
from ralph.dnsedit.models import DHCPEntry
from ralph.util import Eth


def get_next_free_hostname(dc, reserved_hostnames=[]):
    hostnames_in_deployments = Deployment.objects.filter().values_list(
        'hostname', flat=True
    ).order_by('hostname')
    templates = dc.hosts_naming_template.split("|")
    for template in templates:
        match = re.search('<([0-9]+),([0-9]+)>', template)
        if not match:
            return
        min_number = int(match.group(1))
        max_number = int(match.group(2))
        number_len = len(match.group(2))
        regex = template.replace(
            match.group(0),
            "%s[0-9]{%s}" % (str(min_number)[0], number_len - 1)
        )
        next_number = min_number
        try:
            record = Record.objects.filter(
                name__iregex=regex, type='A'
            ).order_by('-name')[0]
            name_match = re.search(
                template.replace(
                    match.group(0),
                    "(%s[0-9]{%s})" % (str(min_number)[0], number_len - 1)
                ),
                record.name
            )
            next_number = int(name_match.group(1)) + 1
            if next_number > max_number:
                continue
        except IndexError:
            pass
        go_to_next_template = False
        next_hostname = template.replace(
            match.group(0), "{0:%s}" % number_len
        ).format(next_number).replace(" ", "0")
        while (next_hostname in reserved_hostnames or
               next_hostname in hostnames_in_deployments):
            next_number += 1
            if next_number > max_number:
                go_to_next_template = True
                break
            next_hostname = template.replace(
                match.group(0), "{0:%s}" % number_len
            ).format(next_number).replace(" ", "0")
        if go_to_next_template:
            continue
        return next_hostname


def get_first_free_ip(network_name, reserved_ip_addresses=[]):
    network = Network.objects.get(name=network_name)
    addresses_in_dhcp = DHCPEntry.objects.filter(
        number__gte=network.min_ip,
        number__lte=network.max_ip
    ).values_list('number', flat=True).order_by('number')
    addresses_in_discovery = IPAddress.objects.filter(
        number__gte=network.min_ip,
        number__lte=network.max_ip
    ).values_list('number', flat=True).order_by('number')
    addresses_in_dns = Record.objects.filter(
        number__gte=network.min_ip,
        number__lte=network.max_ip,
        type='A'
    ).values_list('number', flat=True).order_by('number')
    addresses_in_running_deployments = Deployment.objects.filter(
        status__in=(DeploymentStatus.open, DeploymentStatus.in_progress)
    ).values_list('ip', flat=True).order_by('ip')
    min_ip_number = network.min_ip + network.reserved
    for ip_number in range(min_ip_number, network.max_ip + 1):
        ip_string = str(ipaddr.IPAddress(ip_number))
        if (ip_number not in addresses_in_dhcp and
            ip_number not in addresses_in_discovery and
            ip_number not in addresses_in_dns and
            ip_string not in addresses_in_running_deployments and
            ip_string not in reserved_ip_addresses):
            return str(ipaddr.IPAddress(ip_number))


def is_mac_address_known(mac):
    return Ethernet.objects.filter(
        mac=MACAddressField.normalize(mac)
    ).exists()


def rack_exists(sn):
    return Device.objects.filter(
        Q(model__type=DeviceType.rack) |
        Q(model__type=DeviceType.blade_system),
        Q(sn=sn)
    ).exists()


def venture_and_role_exists(venture_symbol, venture_role_name):
    return VentureRole.objects.filter(
        venture__symbol=venture_symbol,
        name=venture_role_name
    ).exists()


def preboot_exists(name):
    return Preboot.objects.filter(name=name).exists()


def hostname_exists(hostname):
    return any((
        Record.objects.filter(name=hostname, type='A').exists(),
        Deployment.objects.filter(hostname=hostname).exists()
    ))


def ip_address_exists(ip):
    number = int(ipaddr.IPAddress(ip))
    return any((
        DHCPEntry.objects.filter(number=number).exists(),
        IPAddress.objects.filter(number=number).exists(),
        Record.objects.filter(number=number, type='A').exists(),
        Deployment.objects.filter(
            ip=ip,
            status__in=(DeploymentStatus.open, DeploymentStatus.in_progress)
        ).exists()
    ))


def network_exists(name):
    return Network.objects.filter(name=name).exists()


def management_ip_unique(ip):
    return not IPAddress.objects.filter(address=ip).exists()


def _create_device(data):
    ethernets = [Eth(
        'DEPLOYMENT MAC',
        MACAddressField.normalize(data['mac']),
        EthernetSpeed.unknown
    )]
    dev = Device.create(
        ethernets=ethernets, model_type=DeviceType.unknown,
        model_name='Unknown',
        verified=True,
    )
    dev.name = data['hostname']
    try:
        dev.parent = Device.objects.get(sn=data['rack_sn'])
    except Device.DoesNotExist:
        pass
    dev.save()
    IPAddress.objects.create(
        address=data['ip'],
        device=dev,
        hostname=data['hostname'],
    )
    if management_ip_unique(data['management_ip']):
        IPAddress.objects.create(
            address=data['management_ip'],
            device=dev,
            is_management=True
        )
    return dev


@nested_commit_on_success
def create_deployments(data, user, mass_deployment):
    for item in data:
        mac = MACAddressField.normalize(item['mac'])
        try:
            dev = Device.objects.get(ethernet__mac=mac)
        except Device.DoesNotExist:
            dev = _create_device(item)
        Deployment.objects.create(
            user=user,
            device=dev,
            mac=mac,
            ip=item['ip'],
            hostname=item['hostname'],
            preboot=item['preboot'],
            venture=item['venture'],
            venture_role=item['venture_role'],
            mass_deployment=mass_deployment,
        )
