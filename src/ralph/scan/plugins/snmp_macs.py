# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from django.conf import settings

from ralph.discovery.models import DeviceType, MAC_PREFIX_BLACKLIST
from ralph.discovery.snmp import snmp_macs
from ralph.scan.plugins import get_base_result_template

SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})


class Error(Exception):
    pass


def _get_model_info(snmp_name):
    is_management = False
    if snmp_name.lower().startswith('sunos'):
        model_name = 'SunOs'
        model_type = DeviceType.unknown
    elif snmp_name.lower().startswith('hardware:') and 'Windows' in snmp_name:
        model_name = 'Windows'
        model_type = DeviceType.unknown
    elif snmp_name.startswith('IronPort'):
        model_name = snmp_name.split(',')[0].strip()
        model_type = DeviceType.smtp_gateway
        is_management = True
    elif snmp_name.startswith('IBM PowerPC CHRP Computer'):
        model_name = 'IBM pSeries'
        model_type = DeviceType.unknown
    elif 'Software:UCOS' in snmp_name:
        model_name = 'Cisco UCOS'
        model_type = DeviceType.appliance
        is_management = True
    elif snmp_name.startswith('Codian'):
        model_name = snmp_name
        model_type = DeviceType.appliance
        is_management = True
    elif snmp_name.startswith('APC'):
        m = re.search(r'\sMN:\s*(\S+)', snmp_name)
        model_name = m.group(1) if m else 'APC'
        is_management = True
        model_type = DeviceType.power_distribution_unit
    elif ('fibre channel switch' in snmp_name.lower() or
          'san switch module' in snmp_name.lower()):
        model_name = snmp_name
        model_type = DeviceType.fibre_channel_switch
        is_management = True
    elif ('ethernet switch module' in snmp_name.lower() or
          snmp_name.startswith('ProCurve')):
        model_name = snmp_name
        if ',' in model_name:
            model_name, trash = model_name.split(',', 1)
        model_type = DeviceType.switch
        is_management = True
    elif 'StorageWorks' in snmp_name:
        model_name = snmp_name
        model_type = DeviceType.storage
    elif 'linux' in snmp_name.lower():
        model_name = 'Linux'
        model_type = DeviceType.unknown
    else:
        raise Error(
            "The SNMP name %r doesn't match any supported device."
        )
    return model_name, model_type, is_management


def _snmp_mac(ip_address, snmp_name, snmp_community, snmp_version,
              messages=[]):
    oid = (1, 3, 6, 1, 2, 1, 2, 2, 1, 6)
    sn = None
    if not snmp_name or not snmp_community:
        raise Error(
            "Empty SNMP name or community. "
            "Please perform an autoscan of this address first."
        )
        return
    model_name, model_type, is_management = _get_model_info(snmp_name)
    if snmp_name.startswith('IronPort'):
        parts = snmp_name.split(',')
        pairs = dict(
            (k.strip(), v.strip()) for (k, v) in (
                part.split(':') for part in parts if ':' in part
            )
        )
        sn = pairs.get('Serial #')
    if snmp_name.startswith('APC'):
        m = re.search(r'\sSN:\s*(\S+)', snmp_name)
        if m:
            sn = m.group(1)
    mac_addresses = set()
    for mac in snmp_macs(
        ip_address,
        snmp_community,
        oid,
        attempts=2,
        timeout=3,
        snmp_version=snmp_version,
    ):
        # Skip virtual devices
        if mac[0:6] in MAC_PREFIX_BLACKLIST:
            continue
        if snmp_name.startswith('Brocade') and not mac.startswith('00051E'):
            # Only use the first right mac of the Brocade switches,
            # the rest is trash.
            continue
        if model_name == 'Windows' and mac.startswith('000C29'):
            # Skip VMWare interfaces on Windows
            continue
        if mac.startswith('0001D7') and model_type != DeviceType.load_balancer:
            raise Error("This is an F5.")
        mac_addresses.add(mac)
    if not mac_addresses:
        raise Error("No valid MAC addresses in the SNMP response.")

    result = {
        'type': str(model_type),
        'model_name': model_name,
        'mac_addresses': list(mac_addresses),
    }
    if sn:
        result.update(sn=sn)
    if is_management:
        result['management_ip_addresses'] = [ip_address]
        if model_name.lower() == 'linux':
            result['system_family'] = "Linux"
        elif model_name.lower() == 'sunos':
            result['system_family'] = "Sun"
    else:
        result['system_ip_addresses'] = [ip_address]

    return result


def scan_address(ip_address, **kwargs):
    snmp_name = kwargs.get('snmp_name', '')
    snmp_version = kwargs.get('snmp_version', '2c') or '2c'
    if snmp_version == '3':
        snmp_community = SETTINGS['snmp_v3_auth']
    else:
        snmp_community = str(kwargs['snmp_community'])
    messages = []
    result = get_base_result_template('snmp_macs', messages)
    try:
        device_info = _snmp_mac(
            ip_address,
            snmp_name,
            snmp_community,
            snmp_version,
            messages,
        )
    except Error as e:
        messages.append(unicode(e))
        result.update(status="error")
    else:
        result.update({
            'status': 'success',
            'device': device_info,
        })
    return result
