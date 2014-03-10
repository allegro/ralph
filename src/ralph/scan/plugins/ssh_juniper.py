# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings

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


def _get_switches(ssh):
    stacked = False
    switches = []
    data_reading = False
    for line in _ssh_lines(ssh, 'show virtual-chassis'):
        if all((
            'preprovisioned virtual chassis' in line.lower(),
            not data_reading,
        )):
            stacked = True
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
    return stacked, switches


def _ssh_juniper(ssh, ip_address):
    stacked, switches = _get_switches(ssh)
    if stacked:
        device_type = DeviceType.switch_stack.raw
    else:
        device_type = DeviceType.switch.raw
    device = {
        'type': device_type,
        'system_ip_address': [ip_address],
    }
    if stacked:
        subdevices = []
        for switch in switches:
            subdevices.append({
                'type': DeviceType.switch.raw,
                'model_name': switch['model'],
                'serial_number': switch['serial_number'],
            })
        device['subdevices'] = subdevices
    elif switches:
        device['model_name'] = switches[0]['model']
        device['serial_number'] = switches[0]['serial_number']
    # TODO: hostname, mac...
    return device


def scan_address(ip_address, **kwargs):
    http_family = kwargs.get('http_family', '')
    if http_family and http_family.strip().lower() not in ('juniper',):
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
