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
from django import forms


def _get_next_hostname_number(hostname, template, iteration_definition,
                              min_number, number_len):
    name_match = re.search(
        template.replace(
            iteration_definition,
            "(%s[0-9]{%s})" % (str(min_number)[0], number_len - 1)
        ),
        hostname
    )
    return int(name_match.group(1)) + 1


def get_next_free_hostname(environment, reserved_hostnames=[]):
    hostnames_in_deployments = Deployment.objects.filter().values_list(
        'hostname', flat=True
    ).order_by('hostname')
    templates = environment.hosts_naming_template.split("|")
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
        dns_next_number = min_number
        try:
            record = Record.objects.filter(
                name__iregex=regex, type='A'
            ).order_by('-name')[0]
            dns_next_number = _get_next_hostname_number(
                record.name,
                template,
                match.group(0),
                min_number,
                number_len
            )
        except IndexError:
            pass
        dns_ptr_next_number = min_number
        try:
            record = Record.objects.filter(
                content__iregex=regex, type='PTR'
            ).order_by('-content')[0]
            dns_ptr_next_number = _get_next_hostname_number(
                record.content,
                template,
                match.group(0),
                min_number,
                number_len
            )
        except IndexError:
            pass
        discovery_next_number = min_number
        try:
            device = Device.objects.filter(
                name__iregex=regex
            ).order_by('-name')[0]
            discovery_next_number = _get_next_hostname_number(
                device.name,
                template,
                match.group(0),
                min_number,
                number_len
            )
        except IndexError:
            pass
        next_number = max(
            dns_next_number,
            dns_ptr_next_number,
            discovery_next_number,
        )
        if next_number > max_number:
            continue
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
    max_ip_number = network.max_ip - network.reserved_top_margin
    for ip_number in range(min_ip_number, max_ip_number + 1):
        ip_string = str(ipaddr.IPAddress(ip_number))
        if all((
            ip_number not in addresses_in_dhcp,
            ip_number not in addresses_in_discovery,
            ip_number not in addresses_in_dns,
            ip_string not in addresses_in_running_deployments,
            ip_string not in reserved_ip_addresses,
            not Record.objects.filter(
                name='%s.in-addr.arpa' % '.'.join(
                    reversed(ip_string.split('.')),
                ),
                type='PTR',
            ).exists(),
        )):
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
        Record.objects.filter(content=hostname, type='PTR').exists(),
        Deployment.objects.filter(hostname=hostname).exists(),
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


def clean_hostname(hostname):
    hostname = hostname.strip().lower()
    if '.' not in hostname:
        raise forms.ValidationError("Hostname has to include the domain.")
    try:
        ipaddr.IPAddress(hostname)
    except ValueError:
        return hostname
    raise forms.ValidationError("IP address can't be hostname")
