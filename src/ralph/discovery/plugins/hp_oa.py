#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import hashlib
from urllib2 import urlopen, URLError
import httplib

from lck.django.common import nested_commit_on_success
from lck.django.common.models import MACAddressField
from lck.lang import Null, nullify
from lck.xml import etree_to_dict
import lck.xml.converters
from lxml import etree as ET

from ralph.discovery.models import (IPAddress, Device, DeviceType,
        SERIAL_BLACKLIST, ComponentType, GenericComponent, ComponentModel)
from ralph.util import network, plugin, Eth



SAVE_PRIORITY = 5


def _nullify(value):
    if value is not None:
        raise ValueError
    return Null

def hp_xmldata(hostname, timeout=10):
    try:
        url = urlopen("https://{}/xmldata?item=all".format(hostname),
            timeout=timeout)
        try:
            data = url.read()
        finally:
            url.close()
    except (URLError, httplib.InvalidURL, httplib.BadStatusLine):
        return None, ''
    else:
        if not url.info().get('Content-Type', '').startswith('text/xml'):
            return None, ''
        data = data.decode('utf-8', 'replace').encode('utf-8')
        rimp = ET.fromstring(data)
        if rimp.tag.upper() != 'RIMP':
            return None, data
        return nullify(etree_to_dict(rimp, _converters=[_nullify, int, float,
            lck.xml.converters._datetime,
            lck.xml.converters._datetime_strip_tz]))[1], data


def _get_ethernets(data):
    for mezz in data['PORTMAP']['MEZZ']:
        name = mezz['DEVICE']['NAME']
        ports = mezz['DEVICE']['PORT']
        if isinstance(ports, dict):
            ports = [ports]
        for port in ports:
            if port['TYPE'] == 'INTERCONNECT_TYPE_ETH':
                try:
                    mac = MACAddressField.normalize(port['WWPN'])
                except ValueError:
                    continue
                yield Eth(name, mac, speed=None)


@nested_commit_on_success
def _add_hp_oa_devices(devices, device_type, parent=None):
    if devices and not isinstance(devices, list):
        devices = [devices]
    for i, device in enumerate(devices):
        bay = device['BAY']['CONNECTION2']['BLADESYMBOLICNUMBER'] or str(device['BAY']['CONNECTION'])
        name = device['PN'].strip() or device['SPN'].strip()
        if not name.startswith('HP'):
            name = 'HP ' + name
        firmware = str(device.get('FWRI', ''))
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

        ip_address, created = IPAddress.concurrent_get_or_create(address=str(ip))
        if created:
            ip_address.hostname = network.hostname(ip_address.address)
            ip_address.snmp_name = name
            ip_address.save(update_last_seen=True) # no priorities for IP addresses

        if device_type == DeviceType.management:
            ip_address.is_management = True
            if  parent and not parent.management:
                parent.management = ip_address
                parent.save(priority=SAVE_PRIORITY)
            extra = name
            model, mcreated = ComponentModel.concurrent_get_or_create(
                    type=ComponentType.management.id,
                    extra_hash=hashlib.md5(extra).hexdigest(), extra=extra)
            model.name = name
            model.save(priority=SAVE_PRIORITY)
            component, created = GenericComponent.concurrent_get_or_create(
                    device=parent, sn=sn)
            component.model = model
            component.label = name
            component.save(priority=SAVE_PRIORITY)

            if ip:
                ip_address.is_management = True
                ip_address.device = parent
                ip_address.save() # no priorities for IP addresses

            continue

        if device_type == DeviceType.switch and 'SAN' in name:
            device_type = DeviceType.fibre_channel_switch

        ethernets = list(_get_ethernets(device))
        if not (ip and name and (sn or ethernets)):
            continue

        dev = None

        if ip and device_type in (DeviceType.switch, DeviceType.fibre_channel_switch):
            ip_addr, ip_created = IPAddress.concurrent_get_or_create(address=ip)
            if ip_addr.device:
                dev = ip_addr.device
                dev.parent = parent

        if dev is None:
            dev = Device.create(sn=sn, model_name=name, model_type=device_type,
                            ethernets=ethernets, parent=parent,
                            priority=SAVE_PRIORITY)

        if firmware:
            dev.hard_firmware = firmware
        if bay:
            name = '%s [%s]' % (name, bay)
        if bay:
            if 'A' in bay or 'B' in bay:
                dev.chassis_position = int(bay[:-1])
                if bay[-1] == 'A':
                    dev.chassis_position += 1000
                elif bay[-1] == 'B':
                    dev.chassis_position += 2000
            else:
                dev.chassis_position = int(bay)
            dev.position = bay
        else:
            dev.chassis_position = i + 1
        dev.save(update_last_seen=True, priority=SAVE_PRIORITY)
        ip_address.device = dev
        ip_address.save(update_last_seen=True) # no priorities for IP addresses

def make_encl(data, raw):
    encl_name = data['INFRA2']['PN'].strip()
    encl_sn = data['INFRA2']['ENCL_SN'].strip()
    if not encl_name.startswith('HP'):
        encl_name = 'HP ' + encl_name
    encl = Device.create(sn=encl_sn, name=encl_name, raw=raw,
            model_type=DeviceType.blade_system, model_name=encl_name,
            priority=SAVE_PRIORITY)
    encl.save(update_last_seen=True, priority=SAVE_PRIORITY)
    return encl

@plugin.register(chain='discovery', requires=['ping', 'http'])
def hp_oa_xml(**kwargs):
    snmp_name = kwargs.get('snmp_name', '').lower()
    if snmp_name and "onboard administrator" not in snmp_name:
        return False, "no match.", kwargs
    if kwargs.get('http_family', '') not in ('Unspecified', 'RomPager', 'HP'):
        return False, 'no match.', kwargs
    ip = str(kwargs['ip'])
    data, raw = hp_xmldata(ip, timeout=30)
    if not data:
        return False, 'silent.', kwargs
    # For some reason those are sometimes ints instead of strings
    name = unicode(data['MP']['PN']).strip()
    sn = unicode(data['MP']['SN']).strip()
    rack_name = unicode(data['INFRA2']['RACK']).strip()
    encl_name = unicode(data['INFRA2']['PN']).strip()
    encl_sn = unicode(data['INFRA2']['ENCL_SN']).strip()
    if not (name and sn and rack_name and encl_name and encl_sn):
        return False, 'incompatible answer.', kwargs
    encl = make_encl(data, raw)
    _add_hp_oa_devices(data['INFRA2']['MANAGERS']['MANAGER'],
        DeviceType.management, parent=encl)
    _add_hp_oa_devices(data['INFRA2']['SWITCHES']['SWITCH'],
        DeviceType.switch, parent=encl)
    _add_hp_oa_devices(data['INFRA2']['BLADES']['BLADE'],
        DeviceType.blade_server, parent=encl)
    return True, name, kwargs
