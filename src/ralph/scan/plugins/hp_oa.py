# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import httplib
import lck.xml.converters

from urllib2 import urlopen, URLError

from lck.django.common.models import MACAddressField
from lck.lang import Null, nullify
from lck.xml import etree_to_dict
from lxml import etree as ET

from ralph.discovery.models import (
    DeviceType,
    MAC_PREFIX_BLACKLIST,
    SERIAL_BLACKLIST,
)
from ralph.scan.errors import (
    IncompatibleAnswerError,
    IncompleteAnswerError,
    NoMatchError,
)
from ralph.scan.plugins import get_base_result_template
from ralph.util import network


class Error(Exception):
    pass


def _nullify(value):
    if value is not None:
        raise ValueError()
    return Null


def _get_hp_xml_data(ip_address, timeout=10):
    try:
        url = urlopen(
            "https://{}/xmldata?item=all".format(ip_address),
            timeout=timeout,
        )
        try:
            data = url.read()
        finally:
            url.close()
    except (URLError, httplib.InvalidURL, httplib.BadStatusLine) as e:
        raise IncompatibleAnswerError('Incompatible answer (%s).' % unicode(e))
    else:
        if not url.info().get('Content-Type', '').startswith('text/xml'):
            raise IncompatibleAnswerError(
                'Incompatible answer (improper content type).',
            )
        data = data.decode('utf-8', 'replace').encode('utf-8')
        rimp = ET.fromstring(data)
        if rimp.tag.upper() != 'RIMP':
            raise IncompatibleAnswerError(
                'Incompatible answer (unknown content).',
            )
        return nullify(
            etree_to_dict(
                rimp,
                _converters=[
                    _nullify,
                    int,
                    float,
                    lck.xml.converters._datetime,
                    lck.xml.converters._datetime_strip_tz
                ],
            )
        )[1]


def _get_parent_device(data):
    # For some reason those are sometimes ints instead of strings...
    rack_name = unicode(data['INFRA2']['RACK']).strip()
    encl_name = unicode(data['INFRA2']['PN']).strip()
    encl_sn = unicode(data['INFRA2']['ENCL_SN']).strip()
    if not (rack_name and encl_name and encl_sn):
        raise IncompleteAnswerError(
            'Received an incomplete answer (required values: RACK, PN '
            'and ENCL_SN).',
        )
    if not encl_name.startswith('HP'):
        encl_name = 'HP ' + encl_name
    result = {
        'type': DeviceType.blade_system.raw,
        'model_name': encl_name,
        'rack': rack_name,
    }
    if encl_sn not in SERIAL_BLACKLIST:
        result['serial_number'] = encl_sn
    return result


def _get_mac_addresses(data):
    mac_addresses = []
    for mezz in data['PORTMAP']['MEZZ']:
        ports = mezz['DEVICE']['PORT']
        if isinstance(ports, dict):
            ports = [ports]
        for port in ports:
            if port['TYPE'] == 'INTERCONNECT_TYPE_ETH':
                try:
                    mac = MACAddressField.normalize(port['WWPN'])
                except ValueError:
                    continue
                else:
                    if mac[:6] not in MAC_PREFIX_BLACKLIST:
                        mac_addresses.append(mac)
    return mac_addresses


def _handle_subdevices(device_info, data):
    for devices_data, devices_type in (
        (data['INFRA2']['MANAGERS']['MANAGER'], DeviceType.management),
        (data['INFRA2']['SWITCHES']['SWITCH'], DeviceType.switch),
        (data['INFRA2']['BLADES']['BLADE'], DeviceType.blade_server),
    ):
        if devices_data and not isinstance(devices_data, list):
            devices_data = [devices_data]
        for i, device in enumerate(devices_data):
            bay = device['BAY']['CONNECTION2'][
                'BLADESYMBOLICNUMBER',
            ] or str(device['BAY']['CONNECTION'])
            name = device['PN'].strip() or device['SPN'].strip()
            if not name.startswith('HP'):
                name = 'HP ' + name
            sn = device['SN'].strip()
            if sn in SERIAL_BLACKLIST:
                sn = None
            if not sn:
                sn = device['BSN'].strip()
            if sn in SERIAL_BLACKLIST:
                sn = None
            try:
                ip = network.validate_ip(device['MGMTIPADDR'])
            except ValueError:
                continue
            if devices_type == DeviceType.management:
                management_ip_addresses = set(
                    device_info.get(
                        'management_ip_addresses', [],
                    ),
                )
                management_ip_addresses.add(ip)
                device_info.update(
                    management_ip_addresses=list(management_ip_addresses),
                )
                if 'parts' not in device_info:
                    device_info['parts'] = []
                device_info['parts'].append({
                    'type': devices_type.raw,
                    'model_name': name,
                    'serial_number': sn,
                    'label': name,
                })
                continue
            current_device_type = devices_type
            if devices_type == DeviceType.switch and 'SAN' in name:
                current_device_type = DeviceType.fibre_channel_switch
            mac_addresses = _get_mac_addresses(device)
            if not (ip and name and (sn or mac_addresses)):
                continue
            subdevice = {
                'type': current_device_type.raw,
                'model_name': name,
            }
            if sn:
                subdevice['serial_number'] = sn
            if mac_addresses:
                subdevice['mac_addresses'] = mac_addresses
            if bay:
                if 'A' in bay or 'B' in bay:
                    subdevice['chassis_position'] = int(bay[:-1])
                    if bay[-1] == 'A':
                        subdevice['chassis_position'] += 1000
                    elif bay[-1] == 'B':
                        subdevice['chassis_position'] += 2000
                else:
                    subdevice['chassis_position'] = int(bay)
                subdevice['position'] = bay
            else:
                subdevice['chassis_position'] = i + 1
            subdevices = device_info.get('subdevices', [])
            subdevices.append(subdevice)
            device_info['subdevices'] = subdevices


def _hp_oa(ip_address):
    data = _get_hp_xml_data(ip_address)
    device_info = _get_parent_device(data)
    _handle_subdevices(device_info, data)
    return device_info


def scan_address(ip_address, **kwargs):
    snmp_name = (kwargs.get('snmp_name', '') or '').lower()
    if snmp_name and "onboard administrator" not in snmp_name:
        raise NoMatchError('It is not HP OA.')
    if kwargs.get('http_family', '') not in ('Unspecified', 'RomPager', 'HP'):
        raise NoMatchError('It is not HP OA.')
    messages = []
    result = get_base_result_template('hp_oa', messages)
    try:
        device_info = _hp_oa(ip_address)
    except (IncompatibleAnswerError, IncompleteAnswerError) as e:
        messages.append(unicode(e))
        result['status'] = 'error'
    else:
        result['status'] = 'success'
        result['device'] = device_info
    return result
