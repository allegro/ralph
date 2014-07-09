# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings
from lck.django.common.models import MACAddressField

from ralph.discovery.models import DeviceType, SERIAL_BLACKLIST, DiskShare
from ralph.scan.errors import ConnectionError, NoMatchError
from ralph.scan.plugins import get_base_result_template
from ralph.util import parse
from ralph.util.network import connect_ssh, check_tcp_port


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})


def _connect_ssh(ip_address, user, password):
    if not check_tcp_port(ip_address, 22):
        raise ConnectionError('Port 22 closed on an ONStor  server.')
    return connect_ssh(ip_address, user, password)


def _convert_unit(size_string):
    """
    Convert given string to size in megabytes

    :param string size_string: Size with unit
    :returns integer: Converted size from given unit
    :rtype integer:
    """
    size, unit = size_string.split(' ')
    if 'M' in unit:
        return int(float(size))
    elif 'G' in unit:
        return int(float(size)) * 1024
    elif 'T' in unit:
        return int(float(size)) * 1024 * 1024


def _get_wwn(string):
    """
    Extract part of wwn from given string and try find full wwn

    :param string string: Name contains part of wwn
    :returns string: Full wwn or part
    :rtype string:
    """
    wwn_part = string.split('_')[-1]
    try:
        return DiskShare.objects.get(wwn__contains=wwn_part).wwn
    except (DiskShare.DoesNotExist, DiskShare.MultipleObjectsReturned):
        return wwn_part


def _get_disk_share(ssh):
    """
    Collect wwns from onstor server

    :param object ssh: ssh connection
    :returns list: List of dicts contains data for create share mount
    :rtype list:
    """
    disk_shares = []
    stdin, stdout, stderr = ssh.exec_command("scsi show all")
    for line in stdout.readlines():
        splited_line = line.split()
        if splited_line and splited_line[-2] == 'OPENED':
            stdin_details, stdout_details, stderr_details = ssh.exec_command(
                "scsi show detail {0}".format(splited_line[1])
            )
            pairs = parse.pairs(lines=stdout_details.readlines())
            disk_shares.append(
                {
                    'serial_number': _get_wwn(splited_line[1]),
                    'size': _convert_unit(pairs['CAPACITY']),
                    'volume': None,
                }
            )
    return disk_shares


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
            'mac_addresses': [MACAddressField.normalize(mac)],
        })
        if sn not in SERIAL_BLACKLIST:
            device_info['serial_number'] = sn
        disk_shares = _get_disk_share(ssh)
        if disk_shares:
            device_info['disk_shares'] = disk_shares
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
