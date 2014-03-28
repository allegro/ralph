#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from django.conf import settings

from ralph.util import plugin, Eth
from ralph.discovery.models import (DeviceType, Device, IPAddress,
                                    OperatingSystem)
from ralph.discovery.models import MAC_PREFIX_BLACKLIST
from ralph.discovery.snmp import snmp_command, snmp_macs, check_snmp_port


SAVE_PRIORITY = 1
SNMP_PLUGIN_COMMUNITIES = getattr(settings, 'SNMP_PLUGIN_COMMUNITIES',
                                  ['public'])

SNMP_V3_AUTH = (
    settings.SNMP_V3_USER,
    settings.SNMP_V3_AUTH_KEY,
    settings.SNMP_V3_PRIV_KEY,
)
if not all(SNMP_V3_AUTH):
    SNMP_V3_AUTH = None

_cisco_oids_std = (
    (1, 3, 6, 1, 2, 1, 47, 1, 1, 1, 1, 2, 1001),  # model
    (1, 3, 6, 1, 2, 1, 47, 1, 1, 1, 1, 11, 1001),  # sn
)

_cisco_oids_4500 = (
    (1, 3, 6, 1, 2, 1, 47, 1, 1, 1, 1, 13, 1000),  # model
    (1, 3, 6, 1, 2, 1, 47, 1, 1, 1, 1, 11, 1000),  # sn
)

_cisco_oids_nexus = (
    (1, 3, 6, 1, 2, 1, 47, 1, 1, 1, 1, 13, 149),  # model
    (1, 3, 6, 1, 2, 1, 47, 1, 1, 1, 1, 11, 149),  # sn
)

_cisco_oids = {
    "cisco ios software, c2960": _cisco_oids_std,
    "cisco ios software, c3560": _cisco_oids_std,
    "cisco ios software, c3750e": _cisco_oids_std,
    "cisco ios software, cbs30x0": _cisco_oids_std,
    "cisco ios software, cbs31x0": _cisco_oids_std,
    "cisco ios software, catalyst 4500": _cisco_oids_4500,
    "cisco nx-os(tm) n5000": _cisco_oids_nexus,
    "cisco nx-os(tm) n7000": _cisco_oids_nexus,
}


class Error(Exception):
    pass


def _snmp(ip, community, oid, attempts=2, timeout=3, snmp_version='2c'):
    is_up = False
    result = snmp_command(str(ip), community, oid, attempts=attempts,
                          timeout=timeout, snmp_version=snmp_version)
    if result is None:
        message = 'silent.'
    else:
        message = unicode(result[0][1])
        try:
            ip_address = IPAddress.objects.get(address=str(ip))
        except IPAddress.DoesNotExist:
            message = "IP address not present in DB."
            pass
        else:
            ip_address.snmp_name = message
            ip_address.snmp_community = unicode(community)
            ip_address.save()
            is_up = True
    return is_up, message


@plugin.register(chain='discovery', requires=['ping', 'http'])
def snmp(**kwargs):
    http_family = kwargs.get('http_family')
    if http_family in ('Thomas-Krenn',):
        return False, 'no match.', kwargs
    ip = str(kwargs['ip'])
    if http_family not in ('Microsoft-IIS', 'Unspecified', 'RomPager'):
        # Windows hosts always say that the port is closed, even when it's open
        if not check_snmp_port(ip):
            return False, 'port closed.', kwargs
    community = kwargs.get('community')
    version = kwargs.get('snmp_version')
    oids = [
        ('2c', (1, 3, 6, 1, 2, 1, 1, 1, 0)),  # sysDescr
        # Blade centers answer only to their own OIDs and to SNMP version 1
        #  ('1', (1,3,6,1,4,1,2,3,51,2,2,21,1,1,5,0)),
        # bladeCenterManufacturingId
    ]
    if http_family in ('RomPager',):
        # sysDescr, snmp version 1
        oids.append(('1', (1, 3, 6, 1, 2, 1, 1, 1, 0)))
    if version != '3':
        # Don't try SNMP v2 if v3 worked on this host.
        communities = SNMP_PLUGIN_COMMUNITIES[:]
        if community:
            if community in communities:
                communities.remove(community)
            communities.insert(0, community)
        for community in communities:
            for ver, oid in oids:
                version = ver
                is_up, message = _snmp(
                    ip,
                    community,
                    oid,
                    attempts=2,
                    timeout=0.2,
                    snmp_version=version,
                )
                if message == '' and ver != '1':
                    version = '1'
                    is_up, message = _snmp(
                        ip,
                        community,
                        oid,
                        attempts=2,
                        timeout=0.2,
                        snmp_version=version,
                    )
                # prevent empty response for some communities.
                if message and is_up:
                    kwargs['community'] = community
                    kwargs['snmp_version'] = version
                    kwargs['snmp_name'] = message
                    return is_up, message, kwargs
    if SNMP_V3_AUTH and version not in ('1', '2', '2c'):
        is_up, message = _snmp(
            ip, SNMP_V3_AUTH,
            (1, 3, 6, 1, 2, 1, 1, 1, 0),
            attempts=2,
            timeout=0.5,  # SNMP v3 usually needs more time
            snmp_version='3',
        )
        if is_up:
            kwargs['community'] = ''
            kwargs['snmp_version'] = '3'
            kwargs['snmp_name'] = message
            return is_up, message, kwargs
    kwargs['community'] = ''
    kwargs['snmp_version'] = ''
    return False, 'no answer.', kwargs


def _snmp_modular(ip, community, parent):
    oid = (1, 3, 6, 1, 4, 1, 343, 2, 19, 1, 2, 10, 12, 0)  # Max blades
    message = snmp_command(ip, community, oid, attempts=1, timeout=0.5)
    max_blades = int(message[0][1])
    blades_macs = {}
    for blade_no in range(1, max_blades + 1):
        oid = (1, 3, 6, 1, 4, 1, 343, 2, 19, 1, 2, 10, 202, 3, 1, 1, blade_no)
        blades_macs[blade_no] = set(snmp_macs(ip, community, oid,
                                    attempts=1, timeout=0.5))
    for i, macs in blades_macs.iteritems():
        unique_macs = macs
        for j, other_macs in blades_macs.iteritems():
            if i == j:
                continue
            unique_macs -= other_macs
        ethernets = [Eth('Intel Modular MAC', mac, speed=None) for mac in
                     unique_macs]
        if ethernets:
            dev = Device.create(
                name='Intel Modular Blade',
                model_name='Intel Modular Blade',
                model_type=DeviceType.blade_server,
                ethernets=ethernets,
                management=parent.management,
                chassis_position=i,
                position=str(i),
                parent=parent,
            )
            dev.save(update_last_seen=True, priority=SAVE_PRIORITY)


def snmp_f5(**kwargs):
    ip = str(kwargs['ip'])
    community = str(kwargs['community'])
    model = str(snmp_command(ip, community,
                             [int(i)
                              for i in '1.3.6.1.4.1.3375.2.1.3.5.2.0'.split('.')],
                             attempts=1, timeout=0.5)[0][1])
    sn = str(snmp_command(ip, community,
                          [int(i)
                           for i in '1.3.6.1.4.1.3375.2.1.3.3.3.0'.split('.')],
                          attempts=1, timeout=0.5)[0][1])
    return 'F5 %s' % model, sn


def snmp_vmware(parent, ipaddr, **kwargs):
    ip = str(kwargs['ip'])
    community = str(kwargs['community'])
    oid = (1, 3, 6, 1, 4, 1, 6876, 2, 4, 1, 7)
    snmp_version = 1
    for mac in snmp_macs(ip, community, oid, attempts=2,
                         timeout=3, snmp_version=snmp_version):
        Device.create(
            parent=parent,
            management=ipaddr,
            ethernets=[Eth(mac=mac, label='Virtual MAC', speed=0)],
            model_name='VMware ESX virtual server',
            model_type=DeviceType.virtual_server,
        )


@plugin.register(chain='discovery', requires=['ping', 'snmp'])
def snmp_mac(**kwargs):
    snmp_name = kwargs.get('snmp_name', '')
    snmp_version = kwargs.get('snmp_version', '2c')
    ip = str(kwargs['ip'])
    if snmp_version == '3':
        community = SNMP_V3_AUTH
    else:
        community = str(kwargs['community'])
    try:
        ethernets = do_snmp_mac(snmp_name, community, snmp_version, ip, kwargs)
    except Error as e:
        return False, str(e), kwargs
    return True, ', '.join(eth.mac for eth in ethernets), kwargs


def do_snmp_mac(snmp_name, community, snmp_version, ip, kwargs):
    oid = (1, 3, 6, 1, 2, 1, 2, 2, 1, 6)
    sn = None
    is_management = False
    if snmp_name.lower().startswith('sunos'):
        model_name = 'SunOs'
        model_type = DeviceType.unknown
    elif snmp_name.lower().startswith('hardware:') and 'Windows' in snmp_name:
        model_name = 'Windows'
        model_type = DeviceType.unknown
    elif snmp_name.lower().startswith('vmware esx'):
        model_name = 'VMware ESX'
        model_type = DeviceType.unknown
        oid = (1, 3, 6, 1, 2, 1, 2, 2, 1, 6)
        snmp_version = 1
    elif snmp_name.startswith('IronPort'):
        parts = snmp_name.split(',')
        model_name = parts[0].strip()
        model_type = DeviceType.smtp_gateway
        is_management = True
    elif snmp_name.startswith('Intel Modular'):
        model_type = DeviceType.blade_system
        model_name = 'Intel Modular Blade System'
        is_management = True
    elif snmp_name.startswith('IBM PowerPC CHRP Computer'):
        model_type = DeviceType.unknown
        model_name = 'IBM pSeries'
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
        m = re.search(r'\sSN:\s*(\S+)', snmp_name)
        sn = m.group(1) if m else None
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
        model_name, sn = snmp_f5(**kwargs)
        model_type = DeviceType.load_balancer
    elif 'StorageWorks' in snmp_name:
        model_name = snmp_name
        model_type = DeviceType.storage
    elif 'linux' in snmp_name.lower():
        model_name = 'Linux'
        model_type = DeviceType.unknown
    else:
        model_name = 'Unknown'
        model_type = DeviceType.unknown
        raise Error('no match.')
    ethernets = []
    for mac in snmp_macs(ip, community, oid, attempts=2,
                         timeout=3, snmp_version=snmp_version):
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
            model_name, sn = snmp_f5(**kwargs)
            model_type = DeviceType.load_balancer
        ethernets.append(Eth('SNMP MAC', mac, speed=None))
    if model_type == DeviceType.load_balancer:
        # For F5, macs that start with 02 are the maqueraded macs
        ethernets = [e for e in ethernets if not e.mac.startswith('02')]
    if not ethernets and not sn:
        raise Error('no MAC.')
    name = snmp_name
    dev = Device.create(ethernets=ethernets, model_name=model_name,
                        model_type=model_type, name=name, sn=sn)
    ip_address, created = IPAddress.concurrent_get_or_create(address=str(ip))
    ip_address.device = dev
    ip_address.is_management = is_management
    if is_management:
        dev.management = ip_address
    if model_name == 'VMware ESX':
        snmp_vmware(dev, ip_address, **kwargs)
    ip_address.save()
    if model_name.startswith('IronPort'):
        pairs = dict((k.strip(), v.strip()) for (k, v) in
                     (part.split(':') for part in parts if ':' in part))
        dev.boot_firmware = 'AsyncOS %s %s' % (
            pairs.get('AsyncOS Version'), pairs.get('Build Date'))
        dev.sn = pairs.get('Serial #')
        dev.save(update_last_seen=True, priority=SAVE_PRIORITY)
    elif model_name == 'Intel Modular Blade System':
        _snmp_modular(ip, community, dev)
    if not dev.operatingsystem_set.exists():
        if model_name in ('Linux', 'SunOs'):
            family = 'Linux' if model_name == 'Linux' else 'Sun'
            OperatingSystem.create(dev, os_name=snmp_name, family=family,
                                   priority=SAVE_PRIORITY)
    return ethernets


def _cisco_snmp_model(model_oid, sn_oid, **kwargs):
    ip = str(kwargs['ip'])
    version = kwargs.get('snmp_version')
    if version == '3':
        community = SNMP_V3_AUTH
    else:
        community = str(kwargs['community'])
    model = snmp_command(
        ip,
        community,
        model_oid,
        attempts=2,
        timeout=3,
        snmp_version=version,
    )
    sn = snmp_command(
        ip,
        community,
        sn_oid,
        attempts=2,
        timeout=3,
        snmp_version=version,
    )
    if not (model and sn):
        return False, "silent.", kwargs
    sn = unicode(sn[0][1])
    model = 'Cisco %s' % unicode(model[0][1])
    dev = Device.create(sn=sn, model_name=model, model_type=DeviceType.switch)
    ip_address, created = IPAddress.concurrent_get_or_create(address=str(ip))
    ip_address.device = dev
    ip_address.is_management = True
    ip_address.save()
    return True, sn, kwargs


@plugin.register(chain='discovery', requires=['ping', 'snmp'])
def cisco_snmp(**kwargs):
    for substring, oids in _cisco_oids.iteritems():
        if ('snmp_name' in kwargs and kwargs['snmp_name'] and
                substring in kwargs['snmp_name'].lower()):
            return _cisco_snmp_model(oids[0], oids[1], **kwargs)
    return False, "no match.", kwargs


@plugin.register(chain='discovery', requires=['ping', 'snmp'])
def juniper_snmp(**kwargs):
    sn_oid = (1, 3, 6, 1, 4, 1, 2636, 3, 1, 3, 0)
    model_oid = (1, 3, 6, 1, 4, 1, 2636, 3, 1, 2, 0)
    version = kwargs.get('snmp_version')
    if version == '3':
        community = SNMP_V3_AUTH
    else:
        community = str(kwargs['community'])
    substring = "juniper networks"
    if not ('snmp_name' in kwargs and kwargs['snmp_name'] and
            substring in kwargs['snmp_name'].lower()):
        return False, "no match.", kwargs
    ip = str(kwargs['ip'])
    sn = snmp_command(
        ip,
        community,
        sn_oid,
        attempts=2,
        timeout=3,
        snmp_version=version,
    )
    model = snmp_command(
        ip,
        community,
        model_oid,
        attempts=2,
        timeout=3,
        snmp_version=version,
    )
    if not sn or not model:
        return False, "silent.", kwargs
    sn = unicode(str(sn[0][1]), encoding='utf-8')
    model = unicode(str(model[0][1]), encoding='utf-8')
    dev = Device.create(sn=sn, model_name=model, model_type=DeviceType.switch)
    ip_address, created = IPAddress.concurrent_get_or_create(address=str(ip))
    ip_address.device = dev
    ip_address.is_management = True
    ip_address.save()
    return True, sn, kwargs


@plugin.register(chain='discovery', requires=['ping', 'snmp'])
def nortel_snmp(**kwargs):
    sn_oid = (1, 3, 6, 1, 4, 1, 1872, 2, 5, 1, 3, 1, 18, 0)
    uuid_oid = (1, 3, 6, 1, 4, 1, 1872, 2, 5, 1, 3, 1, 17, 0)
    substrings = ["nortel layer2-3 gbe switch",
                  "bnt layer 2/3 copper gigabit ethernet "
                  "switch module for ibm bladecenter"]
    snmp_name = kwargs.get('snmp_name', '')
    if not (snmp_name and any(substring in kwargs['snmp_name'].lower()
            for substring in substrings)):
        return False, "no match.", kwargs
    ip = str(kwargs['ip'])
    version = kwargs.get('snmp_version')
    if version == '3':
        community = SNMP_V3_AUTH
    else:
        community = str(kwargs['community'])
    sn = (
        snmp_command(
            ip,
            community,
            sn_oid,
            attempts=2,
            timeout=3,
            snmp_version=version,
        ) or
        snmp_command(
            ip,
            community,
            uuid_oid,
            attempts=2,
            timeout=3,
            snmp_version=version,
        )
    )
    if not sn:
        return False, "silent.", kwargs
    sn = unicode(sn[0][1])
    model = kwargs['snmp_name']
    dev = Device.create(sn=sn, model_name=model, model_type=DeviceType.switch)
    ip_address, created = IPAddress.concurrent_get_or_create(address=str(ip))
    ip_address.device = dev
    ip_address.is_management = True
    ip_address.save()
    kwargs['model'] = model
    kwargs['sn'] = sn
    return True, sn, kwargs
