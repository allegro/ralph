# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from django.db import transaction
from django.db.models import Q
import ipaddr
from lck.django.common.models import MACAddressField
from powerdns.models import Record

from ralph.business.models import VentureRole
from ralph.deployment.models import Preboot, Deployment
from ralph.discovery.models import (
    DataCenter, Network, IPAddress, Ethernet, DeviceType, Device,
    EthernetSpeed,
)
from ralph.dnsedit.models import DHCPEntry
from ralph.util import Eth


def get_nexthostname(dc_name, reserved_hostnames=[]):
    try:
        dc = DataCenter.objects.get(name__iexact=dc_name.lower())
    except DataCenter.DoesNotExist:
        return False, "", "Specified data center doesn't exists."
    templates = dc.hosts_naming_template.split("|")
    for template in templates:
        match = re.search('<([0-9]+),([0-9]+)>', template)
        if not match:
            return False, "", "Incorrect hosts names template in DC: %s" % (
                dc_name
            )
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
        while next_hostname in reserved_hostnames:
            next_number += 1
            if next_number > max_number:
                go_to_next_template = True
                break
            next_hostname = template.replace(
                match.group(0), "{0:%s}" % number_len
            ).format(next_number).replace(" ", "0")
        if go_to_next_template:
            continue
        return True, next_hostname, ""
    return False, "", "Couldn't determine the next host name."


def get_firstfreeip(network_name, reserved_ip_addresses=[]):
    try:
        network = Network.objects.get(name=network_name)
    except Network.DoesNotExist:
        return False, "", "Specified network doesn't exists."
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
    for ip_number in range(network.min_ip + 1, network.max_ip + 1):
        if (ip_number not in addresses_in_dhcp and
            ip_number not in addresses_in_discovery and
            ip_number not in addresses_in_dns and
            str(ipaddr.IPAddress(ip_number)) not in reserved_ip_addresses):
            return True, str(ipaddr.IPAddress(ip_number)), ""
    return False, "", "Couldn't determine the first free IP."


def is_mac_address_unknown(mac):
    return not Ethernet.objects.filter(
        mac=MACAddressField.normalize(mac)
    ).exists()


def is_rack_exists(sn):
    return Device.objects.filter(
        Q(model__type=DeviceType.rack) |
        Q(model__type=DeviceType.blade_system),
        Q(sn=sn)
    ).exists()


def are_venture_and_role_exists(venture_name, venture_role_name):
    return VentureRole.objects.filter(
        venture__name=venture_name,
        name=venture_role_name
    ).exists()


def is_preboot_exists(name):
    return Preboot.objects.filter(name=name).exists()


def is_hostname_exists(hostname):
    return Record.objects.filter(name=hostname, type='A').exists()


def is_ip_address_exists(ip):
    number = int(ipaddr.IPAddress(ip))
    return any((
        DHCPEntry.objects.filter(number=number).exists(),
        IPAddress.objects.filter(number=number).exists(),
        Record.objects.filter(number=number, type='A').exists()
    ))


def is_network_exists(name):
    return Network.objects.filter(name=name).exists()


def is_management_ip_unique(ip):
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
    )
    try:
        dev.parent = Device.objects.get(sn=data['rack_sn'])
        dev.save()
    except Device.DoesNotExist:
        pass
    IPAddress.objects.create(
        address=data['management_ip'],
        device=dev,
        is_management=True
    )
    return dev


@transaction.commit_on_success
def create_deployments(data, user, multiple_deployment):
    for item in data:
        dev = _create_device(item)
        Deployment.objects.create(
            user=user, device=dev, mac=item['mac'], ip=item['ip'],
            hostname=item['hostname'], preboot=item['preboot'],
            venture=item['venture'], venture_role=item['venture_role'],
            multiple_deployment=multiple_deployment
        )
