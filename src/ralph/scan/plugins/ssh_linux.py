# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import paramiko

from django.conf import settings

from ralph.scan.plugins import get_base_result_template
from ralph.util import network, parse


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})


def _parse_dmidecode(data):
    """Parse data returned by the dmidecode command into a dict."""

    parsed_data = parse.multi_pairs(data)

    def exclude(value, exceptions):
        if value not in exceptions:
            return value

    def num(value):
        if value is None or value.lower() == 'unknown':
            return None
        try:
            num, unit = value.split(None, 1)
        except ValueError:
            num = value
        return int(num)

    if 'System Information' not in parsed_data:
        return {}
    return {
        'model_name': parsed_data['System Information']['Product Name'],
        'serial_number': parsed_data['System Information']['Serial Number'],
        'processors': [
            {
                'label': cpu['Socket Designation'],
                'model_name': cpu['Version'],
                'speed': num(cpu['Current Speed']),
                'threads': num(cpu.get('Thread Count')),
                'cores': num(cpu.get('Core Count')),
                'family': cpu['Family'],
                '64bit': any(
                    '64-bit capable' in char
                    for char in cpu.getlist('Characteristics') if char
                ),
                'flags': [
                    f.keys() for f in cpu.getlist('Flags') if f
                ][0] if 'Flags' in cpu else [],
            } for cpu in parsed_data.getlist('Processor Information') if cpu
        ],
        'memmory': [
            {
                'label': mem['Locator'],
                'type': mem['Type'],
                'size': num(mem['Size']),
                'speed': num(exclude(mem.get('Speed'), {'Unknown'})),
            }
            for mem in parsed_data.getlist('Memory Device')
            if mem and mem.get('Size') != 'No Module Installed'
        ],
    }

def _get_mac_addresses(ssh):
    """Get the MAC addresses"""

    stdin, stdout, stderr = ssh.exec_command(
        "/sbin/ip addr show | /bin/grep 'link/ether'",
    )
    return [line.split(None, 3)[1] for line in stdout]


def _get_base_device_info(ssh, messages=[]):
    """Handle dmidecode data"""

    stdin, stdout, stderr = ssh.exec_command(
        "/usr/bin/sudo /usr/sbin/dmidecode",
    )

    device_info = _parse_dmidecode(stdout.read())
    if not device_info:
        messages.append('DMIDECODE: System information not found.')


def _ssh_linux(ssh, messages=[]):
    pass


def scan_address(ip_address, **kwargs):
    messages = []
    result = get_base_result_template('ssh_linux', messages)
    snmp_name = kwargs.get('snmp_name', '').lower()
    if 'nx-os' in snmp_name:
        messages.append('Incompatible Nexus found.')
        result['status'] = 'error'
        return result
    if all((
        'linux' not in snmp_name,
        'xen' not in snmp_name,
        not snmp_name.startswith('vmware esx'),
    )):
        messages.append('No match.')
        result['status'] = 'error'
        return result
    ssh = None
    auths = SETTINGS.get('auths', [])
    for user, password in auths:
        if user is None or password is None:
            continue
        try:
            ssh = network.connect_ssh(ip_address, user, password)
        except network.AuthError:
            continue
        else:
            break
    if not ssh:
        messages.append('Authorization failed')
        result['status'] = 'error'
        return result
    try:
        device_info = _ssh_linux(ssh)
    except (network.Error, paramiko.SSHException) as e:
        messages.append(unicode(e))
        result['status'] = 'error'
    else:
        result.update({
            'status': 'success',
            'device': device_info,
        })
    return result

