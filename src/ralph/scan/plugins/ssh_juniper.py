# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings
from lck.django.common.models import MACAddressField

from ralph.discovery.models import DeviceType
from ralph.scan.errors import (
    ConnectionError,
    NoMatchError,
)
from ralph.scan.plugins import get_base_result_template
from ralph.util.network import check_tcp_port, connect_ssh


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})


def _connect_ssh(ip_address, user, password):
    if not check_tcp_port(ip_address, 22):
        raise ConnectionError('Port 22 closed on a Juniper switch.')
    return connect_ssh(ip_address, user, password)


def _ssh_lines(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    for line in stdout.readlines():
        line = line.strip()
        if not line:
            continue
        yield line


def _get_hostname(ssh):
    for line in _ssh_lines(ssh, 'show version'):
        if line.lower().startswith('hostname'):
            line_chunks = line.split(':')
            try:
                return line_chunks[1].strip()
            except IndexError:
                pass  # unexpected result... maybe next line will be ok...


def _get_mac_addresses(ssh):
    mac_addresses = []
    for line in _ssh_lines(ssh, 'show chassis mac-addresses'):
        line = line.lower()
        if line.startswith('public base address'):
            mac_addresses.append(
                MACAddressField.normalize(
                    line.replace('public base address', '').strip()
                )
            )
    return mac_addresses


def _get_switches(ssh):
    stacked = False
    chassis_id = ''
    switches = []
    data_reading = False
    for line in _ssh_lines(ssh, 'show virtual-chassis'):
        if all((
            'preprovisioned virtual chassis' in line.lower(),
            not data_reading,
        )):
            stacked = True
            continue
        if all((
            'virtual chassis id' in line.lower(),
            not data_reading,
        )):
            try:
                chassis_id = line.split(':')[1].strip()
            except IndexError:
                pass
            continue
        if line.lower().startswith('member id') and not data_reading:
            data_reading = True
            continue
        if data_reading:
            line = line.replace('FPC ', '')
            chunks = line.split()
            try:
                sn, model, role = chunks[3], chunks[4], chunks[6]
            except IndexError:
                continue  # incorrect data or end of switches list...
            else:
                switches.append({
                    'serial_number': sn,
                    'model': model,
                    'role': role,
                })
                if not stacked:
                    break
    return stacked, chassis_id, switches


def _ssh_juniper(ssh, ip_address):
    stacked, chassis_id, switches = _get_switches(ssh)
    if stacked:
        device_type = DeviceType.switch_stack.raw
    else:
        device_type = DeviceType.switch.raw
    device = {
        'type': device_type,
        'management_ip_addresses': [ip_address],
    }
    hostname = _get_hostname(ssh)
    mac_addresses = _get_mac_addresses(ssh)
    if hostname:
        device['hostname'] = hostname
    if stacked:
        subdevices = []
        hostname_chunks = hostname.split('.', 1)
        try:
            hostname_base, hostname_domain = (
                hostname_chunks[0], hostname_chunks[1],
            )
        except IndexError:
            hostname_base, hostname_domain = None, None
        for switch, i in zip(switches, xrange(0, len(switches))):
            subdevice = {
                'type': DeviceType.switch.raw,
                'model_name': switch['model'],
                'serial_number': switch['serial_number'],
                'mac_addresses': [
                    mac_addresses[i]
                ] if mac_addresses else []
            }
            if hostname_base and hostname_domain:
                subdevice['hostname'] = '{}-{}.{}'.format(
                    hostname_base, i, hostname_domain
                )
            subdevices.append(subdevice)
        device['subdevices'] = subdevices
        device['model_name'] = 'Juniper Virtual Chassis Ethernet Switch'
        device['serial_number'] = chassis_id
    elif switches:
        device['model_name'] = switches[0]['model']
        device['serial_number'] = switches[0]['serial_number']
        if mac_addresses:
            device['mac_addresses'] = [mac_addresses[0]]
    return device


def scan_address(ip_address, **kwargs):
    snmp_name = (kwargs.get('snmp_name', '') or '')
    http_family = (kwargs.get('http_family', '') or '')
    if ((snmp_name and 'juniper' not in snmp_name.lower()) and
            (http_family and http_family.strip().lower() not in ('juniper',))):
        raise NoMatchError('It is not Juniper.')
    user = SETTINGS.get('user')
    password = SETTINGS.get('password')
    messages = []
    result = get_base_result_template('ssh_juniper', messages)
    if not user or not password:
        result['status'] = 'error'
        messages.append(
            'Not configured. Set SSH_SSG_USER and SSH_SSG_PASSWORD in your '
            'configuration file.',
        )
    else:
        try:
            ssh = _connect_ssh(ip_address, user, password)
        except ConnectionError as e:
            result['status'] = 'error'
            messages.append(unicode(e))
        else:
            try:
                device_info = _ssh_juniper(ssh, ip_address)
            finally:
                ssh.close()
            result.update({
                'status': 'success',
                'device': device_info,
            })
    return result
