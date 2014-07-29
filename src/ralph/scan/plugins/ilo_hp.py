# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from django.conf import settings
from lck.django.common.models import MACAddressField

from ralph.discovery import hp_ilo
from ralph.discovery.models import (
    ComponentType,
    DeviceType,
    MAC_PREFIX_BLACKLIST,
    SERIAL_BLACKLIST
)
from ralph.scan.errors import NoMatchError
from ralph.scan.plugins import get_base_result_template


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})


logger = logging.getLogger(__name__)


def _get_base_device_info(ilo):
    if ilo.model.startswith('HP ProLiant BL'):
        model_type = DeviceType.blade_server.raw
    else:
        model_type = DeviceType.rack_server.raw
    result = {
        'type': model_type,
        'model_name': ilo.model,
        'parts': [{
            'mgmt_firmware': ilo.firmware,
            'type': ComponentType.management.raw,
        }],
    }
    if ilo.sn not in SERIAL_BLACKLIST:
        result['serial_number'] = ilo.sn
    return result


def _get_mac_addresses(ilo):
    return [
        MACAddressField.normalize(mac)
        for _, mac in ilo.ethernets
        if mac.replace(':', '').upper()[:6] not in MAC_PREFIX_BLACKLIST
    ]


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
    try:
        ilo.update()
    except hp_ilo.AuthError as e:
        logger.warning('%s\t\t%s' % (ip_address, e.message))
        raise e
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
    if kwargs.get('http_family', '') not in ('Unspecified', 'RomPager', 'HP'):
        raise NoMatchError('It is not HP.')
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
