# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings

from ralph.discovery.models import DeviceType, SERIAL_BLACKLIST
from ralph.scan.errors import ConnectionError, NoMatchError
from ralph.scan.plugins import get_base_result_template
from ralph.util import parse
from ralph.util.network import connect_ssh, check_tcp_port


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})


def _connect_ssh(ip_address, user, password):
    if not check_tcp_port(ip_address, 22):
        raise ConnectionError('Port 22 closed on an ONStor  server.')
    return connect_ssh(ip_address, user, password)


def _ssh_onstor(ip_address, user, password):
    device_info = {
        'type': DeviceType.storage.raw,
        'management_ip_addresses': [ip_address],
    }
    ssh = _connect_ssh(ip_address, user, password)
    try:
        stdin, stdout, stderr = ssh.exec_command("system show summary")
        pairs = parse.pairs(lines=stdout.readlines())
        model_name = pairs['--------']['Model number']
        sn = pairs['--------']['System serial number']
        mac = pairs['--------']['MAC addr'].upper().replace(':', '')
        device_info.update({
            'model_name': 'Onstor %s' % model_name,
            'mac_addresses': [mac],
        })
        if sn not in SERIAL_BLACKLIST:
            device_info['serial_number'] = sn
    finally:
        ssh.close()
    return device_info


def scan_address(ip_address, **kwargs):
    if kwargs.get('http_family') not in ('sscccc',):
        raise NoMatchError("It's not an ONStor.")
    if 'nx-os' in (kwargs.get('snmp_name', '') or '').lower():
        raise NoMatchError("Incompatible Nexus found.")
    user = SETTINGS.get('user')
    password = SETTINGS.get('password')
    messages = []
    result = get_base_result_template('ssh_onstor', messages)
    if not user or not password:
        result['status'] = 'error'
        messages.append(
            'Not configured. Set SSH_ONSTOR_USER and SSH_ONSTOR_PASSWORD in '
            'your configuration file.',
        )
    else:
        try:
            device_info = _ssh_onstor(ip_address, user, password)
        except ConnectionError as e:
            result['status'] = 'error'
            messages.append(unicode(e))
        else:
            result.update({
                'status': 'success',
                'device': device_info,
            })
    return result
