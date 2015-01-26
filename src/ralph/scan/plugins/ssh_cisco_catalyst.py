#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from django.conf import settings
from lck.django.common.models import MACAddressField

from ralph.discovery.cisco import cisco_inventory
from ralph.discovery.models import DeviceType, SERIAL_BLACKLIST
from ralph.scan.errors import (
    ConnectionError,
    NoMatchError,
    NotConfiguredError,
)
from ralph.scan.plugins import get_base_result_template
from ralph.util import network


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})
SSH_USER, SSH_PASSWORD = SETTINGS['ssh_user'], SETTINGS['ssh_pass']


def _connect_ssh(ip, username, password):
    if not network.check_tcp_port(ip, 22):
        raise ConnectionError('Port 22 closed.')
    return network.connect_cisco_ssh(ip, username, password)


def get_subswitches(switch_version, hostname, ip_address):
    base_mac_addresses = [
        MACAddressField.normalize(
            "".join(re.findall('[0-9a-fA-F]{2}', line[25:]))
        )
        for line in switch_version
        if 'Base ethernet MAC Address' in line
    ]
    serial_numbers = [
        "".join(re.findall('[0-9a-zA-Z]+', line[33:]))
        for line in switch_version
        if 'System serial number' in line
    ]
    num_switches = len(base_mac_addresses)
    software_versions = None
    model_names = []
    for i, line in enumerate(switch_version):
        if re.match("Switch\W+Ports\W+Model", line):
            model_names = [
                'Cisco Catalyst ' + re.split("\s+", line)[3]
                for line in switch_version[i + 2:i + 2 + num_switches]
            ]
            software_versions = [
                re.split("\s+", line)[4]
                for line in switch_version[i + 2:i + 2 + num_switches]
            ]
    if len(model_names) < 2:
        # not stacked switch
        return []

    zippd = zip(
        serial_numbers,
        base_mac_addresses,
        model_names,
        software_versions,
    )
    subswitches = []
    if hostname:
        hostname_chunks = hostname.split('.', 1)
        try:
            hostname_base, hostname_domain = (
                hostname_chunks[0], '.%s' % hostname_chunks[1],
            )
        except IndexError:
            hostname_base, hostname_domain = None, None
    else:
        hostname_base, hostname_domain = ip_address, ''
    for i, subs in enumerate(zippd):
        subswitches.append(
            {
                'serial_number': subs[0],
                'mac_addresses': [MACAddressField.normalize(subs[1])],
                'model_name': subs[2],
                'hostname': '%s-%d%s' % (
                    hostname_base, i + 1, hostname_domain),
                'installed_software': [
                    {
                        'version': subs[3],
                    }
                ],
                'type': DeviceType.switch.raw,
            }
        )
    return subswitches


def scan_address(ip_address, **kwargs):
    if 'nx-os' in (kwargs.get('snmp_name', '') or '').lower():
        raise NoMatchError('Incompatible Nexus found.')
    if kwargs.get('http_family') not in ('Unspecified', 'Cisco'):
        raise NoMatchError('It is not Cisco.')
    if not SSH_USER or not SSH_PASSWORD:
        raise NotConfiguredError(
            "SSH not configured in plugin {}.".format(__name__),
        )
    ssh = _connect_ssh(ip_address, SSH_USER, SSH_PASSWORD)
    hostname = network.hostname(ip_address)
    try:
        mac = '\n'.join(ssh.cisco_command(
            "show version | include Base ethernet MAC Address",
        ))
        raw = '\n'.join(ssh.cisco_command("show inventory"))
        subswitches = get_subswitches(
            ssh.cisco_command("show version"), hostname, ip_address
        )
    finally:
        ssh.close()
    matches = re.match(
        'Base ethernet MAC Address\s+:\s*([0-9aA-Z:]+)', mac)
    if matches and matches.groups():
        mac = matches.groups()[0]
    inventory = list(cisco_inventory(raw))
    dev_inv, parts = inventory[0], inventory[1:]
    sn = dev_inv['sn']
    result = get_base_result_template('ssh_cisco_catalyst')

    if subswitches:
        # virtual switch doesn't have own unique id, reuse first from stack
        sn += '-virtual'
        model_name = 'Virtual Cisco Catalyst %s' % dev_inv['pid']
        model_type = DeviceType.switch_stack
    else:
        model_name = 'Cisco Catalyst %s' % dev_inv['pid']
        model_type = DeviceType.switch
    result.update({
        'status': 'success',
        'device': {
            'hostname': hostname if hostname else ip_address,
            'model_name': model_name,
            'type': model_type.raw,
            'management_ip_addresses': [ip_address],
            'parts': [{
                'serial_number': part['sn'],
                'name': part['name'],
                'label': part['descr'],
            } for part in parts],
        },
    })
    if sn not in SERIAL_BLACKLIST:
        result['device']['serial_number'] = sn
    if subswitches:
        result['device']['subdevices'] = subswitches
    else:
        try:
            normalized_mac = MACAddressField.normalize(mac)
        except ValueError:
            pass
        else:
            result['device']['mac_addresses'] = [normalized_mac]
    return result
