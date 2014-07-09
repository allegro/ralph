# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re
import subprocess

from django.conf import settings
from django.utils.encoding import force_unicode
from lck.django.common.models import MACAddressField
from lck.lang import nullify

from ralph.discovery.models import (
    DeviceType,
    MAC_PREFIX_BLACKLIST,
    SERIAL_BLACKLIST,
)
from ralph.scan.errors import Error, AuthError, NoMatchError
from ralph.scan.plugins import get_base_result_template
from ralph.util import parse


CPU_LABEL_REGEX = re.compile(r' +')
CPU_SPEED_REGEX = re.compile(r'(\d+\.\d+)GHZ')
MEM_SPEED_REGEX = re.compile(r'(\d+)GB')
REMOVE_ID_REGEX = re.compile(r'\s*[(][^)]*[)]')
SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})


class IPMITool(object):

    def __init__(self, host, user, password):
        self.host = host
        self.user = user
        self.password = password

    def command(self, command, subcommand, *args):
        command = [
            'ipmitool', '-H', self.host, '-U', self.user, '-P', self.password,
            command, subcommand,
        ]
        if args:
            command.extend(args)
        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        out, err = proc.communicate()
        if proc.returncode and err:
            if err.lower().startswith('invalid user name'):
                raise AuthError('Invalid user name.')
            raise Error('Error calling ipmitool: %s' % err)
        return force_unicode(out)


def _clean(raw):
    if raw:
        stripped = raw
        for strip in " .:-_0":
            stripped = stripped.replace(strip, '')
        if stripped:
            return stripped, True
    return raw, False


def _get_ipmi_fru(ipmitool):
    fru = parse.pairs(ipmitool.command('fru', 'print'))
    # remove (ID XX) from the top-level keys
    fru = dict((REMOVE_ID_REGEX.sub('', k), v) for (k, v) in fru.iteritems())
    return nullify(fru)


def _get_base_info(fru_part):
    model_name, _ = _clean(fru_part['Product Name'])
    sn, _ = _clean(fru_part['Product Serial'])
    if sn in SERIAL_BLACKLIST:
        sn = None
    model_type = DeviceType.rack_server.raw
    if model_name.lower().startswith('ipmi'):
        model_name = None
        model_type = None
    return dict([
        (key, value)
        for (key, value) in {
            'serial_number': sn,
            'type': model_type,
            'model_name': model_name,
        }.items() if value
    ])


def _get_mac_addresses(ipmitool, fru):
    data = parse.pairs(ipmitool.command('lan', 'print'))
    mac_addresses = {data.get('MAC Address')}
    index = 0
    while True:
        ethernet = fru.get('MB/NET{}'.format(index))
        if not ethernet:
            break
        mac_addresses.add(ethernet['Product Serial'])
        index += 1
    return [
        MACAddressField.normalize(mac)
        for mac in mac_addresses
        if mac.replace(':', '').upper()[:6] not in MAC_PREFIX_BLACKLIST
    ]


def _get_components(fru):
    detected_processors = []
    detected_memory = []
    cpu_index = 0
    total_mem_index = 0
    while True:
        cpu = fru.get('MB/P{}'.format(cpu_index))
        if not cpu:
            break
        if 'Product Name' not in cpu:
            cpu_index += 1
            continue
        label = CPU_LABEL_REGEX.sub(' ', cpu['Product Name']).title()
        speed_match = CPU_SPEED_REGEX.search(cpu['Product Name'])
        if speed_match:
            speed = int(float(speed_match.group(1)) * 1000)
        else:
            speed = None
        processor = {
            'index': cpu_index + 1,
            'label': label,
            'family': label,
            'model_name': 'CPU %s%s' % (
                label,
                ' %dMHz' % speed if speed else '',
            ),
        }
        if speed:
            processor['speed'] = speed
        detected_processors.append(processor)
        mem_index = 0
        while True:
            mem = fru.get('MB/P{}/D{}'.format(cpu_index, mem_index))
            if not mem:
                break
            if 'Product Name' not in mem:
                mem_index += 1
                continue
            size_match = MEM_SPEED_REGEX.search(mem['Product Name'])
            if not size_match:
                mem_index += 1
                continue
            detected_memory.append({
                'size': int(size_match.group(1)) * 1024,
                'label': mem['Product Name'],
                'index': total_mem_index + 1,
            })
            mem_index += 1
            total_mem_index += 1
        cpu_index += 1
    return detected_processors, detected_memory


def _ipmi(ipmitool):
    try:
        fru = _get_ipmi_fru(ipmitool)
    except AuthError:
        ipmitool = IPMITool(ipmitool.host, 'ADMIN')
        try:
            fru = _get_ipmi_fru(ipmitool)
        except AuthError:
            ipmitool = IPMITool(ipmitool.host, 'ADMIN', 'ADMIN')
            fru = _get_ipmi_fru(ipmitool)
    top = fru['/SYS']
    if not top:
        top = fru['Builtin FRU Device']
    if not top:
        raise Error('Incompatible answer.')
    device_info = _get_base_info(top)
    mac_addresses = _get_mac_addresses(ipmitool, fru)
    if mac_addresses:
        device_info['mac_addresses'] = mac_addresses
    processors, memory = _get_components(fru)
    if processors:
        device_info['processors'] = processors
    if memory:
        device_info['memory'] = memory
    device_info['management_ip_addresses'] = [ipmitool.host]
    return device_info


def scan_address(ip_address, **kwargs):
    http_family = kwargs.get('http_family', '')
    if http_family not in (
        'Sun', 'Thomas-Krenn', 'Oracle-ILOM-Web-Server', 'IBM System X',
    ):
        raise NoMatchError('It is not compatible device for this plugin.')
    user = SETTINGS.get('user')
    password = SETTINGS.get('password')
    messages = []
    result = get_base_result_template('ipmi', messages)
    if not user or not password:
        result['status'] = 'error'
        messages.append('Not configured.')
    else:
        ipmitool = IPMITool(ip_address, user, password)
        try:
            device_info = _ipmi(ipmitool)
        except (AuthError, Error) as e:
            result['status'] = 'error'
            messages.append(unicode(e))
        else:
            result.update({
                'status': 'success',
                'device': device_info,
            })
    return result
