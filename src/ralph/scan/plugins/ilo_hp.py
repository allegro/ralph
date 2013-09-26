# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings

from ralph.discovery import hp_ilo
from ralph.discovery.models import DeviceType, ComponentType
from ralph.scan.plugins import get_base_result_template


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})


def _get_base_device_info(ilo):
    if ilo.model.startswith('HP ProLiant BL'):
        model_type = DeviceType.blade_server.raw
    else:
        model_type = DeviceType.rack_server.raw
    return {
        'type': model_type,
        'model_name': ilo.model,
        'serial_number': ilo.sn,
        'parts': [{
            'mgmt_firmware': ilo.firmware,
            'type': ComponentType.management.raw,
        }],
    }


def _get_mac_addresses(ilo):
    return [mac for _, mac in ilo.ethernets]


def _get_processors(ilo):
    processors = []
    for index, (label, speed, cores, extra, family) in enumerate(
        ilo.cpus,
        start=1,
    ):
        processors.append({
            'model_name': 'CPU %s %dMHz, %s-core' % (family, speed, cores),
            'speed': speed,
            'cores': cores,
            'family': family,
            'label': label,
            'index': index,
        })
    return processors


def _get_memory(ilo):
    memory = []
    for index, (label, size, speed) in enumerate(ilo.memories, start=1):
        memory.append({
            'label': label,
            'size': size,
            'speed': speed,
            'index': index,
        })
    return memory


def _ilo_hp(ip_address, user, password):
    ilo = hp_ilo.IloHost(ip_address, user, password)
    ilo.update()
    device_info = _get_base_device_info(ilo)
    device_info['management_ip_addresses'] = [ip_address]
    mac_addresses = _get_mac_addresses(ilo)
    if mac_addresses:
        device_info['mac_addresses'] = mac_addresses
    processors = _get_processors(ilo)
    if processors:
        device_info['processors'] = processors
    memory = _get_memory(ilo)
    if memory:
        device_info['memory'] = memory
    return device_info


def scan_address(ip_address, **kwargs):
    user = SETTINGS.get('user')
    password = SETTINGS.get('password')
    messages = []
    result = get_base_result_template('ilo_hp', messages)
    if not user or not password:
        result['status'] = 'error'
        messages.append(
            'Not configured. Set ILO_USER and ILO_PASSWORD in your '
            'configuration file.',
        )
    else:
        device_info = _ilo_hp(ip_address, user, password)
        result['status'] = 'success'
        result['device'] = device_info
    return result

