# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from django.conf import settings
from lck.django.common.models import MACAddressField

from ralph.discovery.models import DeviceType, MAC_PREFIX_BLACKLIST
from ralph.discovery.snmp import snmp_command, snmp_macs
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
    elif snmp_name.lower().startswith('vmware esx'):
        model_name = 'VMware ESX'
        model_type = str(DeviceType.unknown)
    elif snmp_name.startswith('IronPort'):
        model_name = snmp_name.split(',')[0].strip()
        model_type = DeviceType.smtp_gateway
        is_management = True
    elif snmp_name.startswith('Intel Modular'):
        model_name = 'Intel Modular Blade System'
        model_type = str(DeviceType.blade_system)
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
    elif '.f5app' in snmp_name:
        model_name = snmp_name
        model_type = str(DeviceType.load_balancer)
    elif 'StorageWorks' in snmp_name:
        model_name = snmp_name
        model_type = DeviceType.storage
    elif 'brocade' in snmp_name.lower():
        model_name = snmp_name
        model_type = DeviceType.switch
    elif 'linux' in snmp_name.lower():
        model_name = 'Linux'
        model_type = DeviceType.unknown
    else:
        raise Error(
            "The SNMP name `%s` doesn't match any supported device." % (
                snmp_name,
            ),
        )
    return model_name, model_type, is_management


def _snmp_vmware_macs(ip_address, snmp_community):
    oid = (1, 3, 6, 1, 4, 1, 6876, 2, 4, 1, 7)
    snmp_version = 1
    results = []
    for mac in snmp_macs(ip_address, snmp_community, oid, attempts=2,
                         timeout=3, snmp_version=snmp_version):
        results.append({
            'type': unicode(DeviceType.virtual_server),
            'model_name': 'VMware ESX virtual server',
            'mac_addresses': [MACAddressField.normalize(mac)],
            'management_ip_addresses': [ip_address],
        })
    return results


def _snmp_modular_macs(ip_address, ip_address_is_management, snmp_community):
    oid = (1, 3, 6, 1, 4, 1, 343, 2, 19, 1, 2, 10, 12, 0)  # Max blades
    message = snmp_command(
        ip_address, snmp_community, oid, attempts=1, timeout=0.5,
    )
    max_blades = int(message[0][1])
    blades_macs = {}
    for blade_no in range(1, max_blades + 1):
        oid = (1, 3, 6, 1, 4, 1, 343, 2, 19, 1, 2, 10, 202, 3, 1, 1, blade_no)
        blades_macs[blade_no] = set(
            snmp_macs(
                ip_address, snmp_community, oid, attempts=1, timeout=0.5,
            ),
        )
    results = []
    management_ip_addresses = []
    if ip_address_is_management:
        management_ip_addresses.append(ip_address)
    for i, macs in blades_macs.iteritems():
        unique_macs = macs
        for j, other_macs in blades_macs.iteritems():
            if i == j:
                continue
            unique_macs -= other_macs
        if unique_macs:
            results.append({
                'type': unicode(DeviceType.blade_server),
                'model_name': 'Intel Modular Blade',
                'mac_addresses': [
                    MACAddressField.normalize(mac) for mac in unique_macs
                ],
                'management_ip_addresses': management_ip_addresses,
                'chassis_position': i,
            })
    return results


def _snmp_mac_from_ipv6IfPhysicalAddress(
    ip_address, snmp_name, snmp_community, snmp_version
):
    mac_addresses = set()
    for mac in snmp_macs(
        ip_address,
        snmp_community,
        (1, 3, 6, 1, 2, 1, 55, 1, 5, 1, 8),  # ipv6IfPhysicalAddress
        attempts=2,
        timeout=3,
        snmp_version=snmp_version,
    ):
        mac_addresses.add(MACAddressField.normalize(mac))
    return mac_addresses


def _snmp_mac(ip_address, snmp_name, snmp_community, snmp_version,
              messages=[]):
    oid = (1, 3, 6, 1, 2, 1, 2, 2, 1, 6)
    sn = None
    if not snmp_name or not snmp_community:
        raise Error(
            "Empty SNMP name or community. "
            "Please perform an autoscan of this address first."
        )
    model_name, model_type, is_management = _get_model_info(snmp_name)
    if snmp_name.lower().startswith('vmware esx'):
        oid = (1, 3, 6, 1, 2, 1, 2, 2, 1, 6)
        snmp_version = 1
    elif snmp_name.startswith('IronPort'):
        parts = snmp_name.split(',')
        pairs = dict(
            (k.strip(), v.strip()) for (k, v) in (
                part.split(':') for part in parts if ':' in part
            )
        )
        sn = pairs.get('Serial #')
    elif snmp_name.startswith('APC'):
        m = re.search(r'\sSN:\s*(\S+)', snmp_name)
        if m:
            sn = m.group(1)
    mac_addresses = set()
    ipv6if_mac_addresses = _snmp_mac_from_ipv6IfPhysicalAddress(
        ip_address=ip_address,
        snmp_name=snmp_name,
        snmp_community=snmp_community,
        snmp_version=snmp_version,
    )
    for mac in snmp_macs(
        ip_address,
        snmp_community,
        oid,
        attempts=2,
        timeout=3,
        snmp_version=snmp_version,
    ):
        # cloud hypervisor can return all VMs mac addresses...
        if ipv6if_mac_addresses and mac not in ipv6if_mac_addresses:
            continue
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
            # This is an F5
            model_name = 'F5'
            model_type = DeviceType.load_balancer
        mac_addresses.add(mac)
    if model_type == DeviceType.load_balancer:
        # For F5, macs that start with 02 are the masqueraded macs
        mac_addresses = set([
            mac for mac in mac_addresses if not mac.startswith('02')
        ])
    if not mac_addresses:
        raise Error("No valid MAC addresses in the SNMP response.")
    result = {
        'type': str(model_type),
        'model_name': model_name,
        'mac_addresses': [
            MACAddressField.normalize(mac) for mac in mac_addresses
        ],
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
    subdevices = []
    if model_name == 'VMware ESX':
        subdevices.extend(_snmp_vmware_macs(ip_address, snmp_community))
    if model_name == 'Intel Modular Blade System':
        subdevices.extend(
            _snmp_modular_macs(ip_address, is_management, snmp_community),
        )
    if subdevices:
        result['subdevices'] = subdevices
    return result


def scan_address(ip_address, **kwargs):
    snmp_name = kwargs.get('snmp_name', '') or ''
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
