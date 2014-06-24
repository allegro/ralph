# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings
from lck.django.common.models import MACAddressField

from ralph.discovery.hardware import normalize_wwn
from ralph.discovery.models import DeviceType, SERIAL_BLACKLIST
from ralph.discovery.storageworks import HPSSHClient
from ralph.scan.errors import (
    ConnectionError,
    NoMatchError,
    NotConfiguredError,
)
from ralph.scan.plugins import get_base_result_template
from ralph.util import network


SETTINGS = settings.SCAN_PLUGINS.get(__name__, {})


def _connect_ssh(ip_address, user, password):
    if not network.check_tcp_port(ip_address, 22):
        raise ConnectionError('Port 22 closed on a HP MSA Storage.')
    return network.connect_ssh(
        ip_address,
        user,
        password,
        client=HPSSHClient,
    )


def _handle_shares(volumes):
    return [{
        'serial_number': normalize_wwn(serial),
        'model_name': 'MSA %s disk share' % volume_type,
        'label': label,
        'size': size * 512 / 1024 / 1024,
    } for (label, serial, size, volume_type, speed) in volumes]


def _ssh_hp_msa(ip_address, user, password):
    ssh = _connect_ssh(ip_address, user, password)
    try:
        ssh.hp_command("set cli-parameters api pager off")
        system_xml = ssh.hp_command("show system")
        network_xml = ssh.hp_command("show network-parameters")
        frus_xml = ssh.hp_command("show frus")
        vdisks_xml = ssh.hp_command("show vdisks")
        volumes = []
        for vdisk_xml in vdisks_xml.xpath('OBJECT[@basetype="virtual-disks"]'):
            vdisk_size = int(
                vdisk_xml.xpath('PROPERTY[@name="size-numeric"]/text()')[0]
            )
            name = vdisk_xml.xpath('PROPERTY[@name="name"]/text()')[0]
            vdisk_raw_size = 0
            disks_xml = ssh.hp_command("show disks vdisk %s" % name)
            disk_type = 'unknown'
            disk_rpm = 0
            for disk_xml in disks_xml.xpath('OBJECT[@basetype="drives"]'):
                disk_size = int(
                    disk_xml.xpath('PROPERTY[@name="size-numeric"]/text()')[0]
                )
                try:
                    disk_type = disk_xml.xpath(
                        'PROPERTY[@name="type"]/text()'
                    )[0]
                except IndexError:
                    pass
                try:
                    disk_rpm = int(
                        disk_xml.xpath('PROPERTY[@name="rpm"]/text()')[0]
                    )
                except IndexError:
                    pass
                vdisk_raw_size += disk_size
            volumes_xml = ssh.hp_command("show volumes vdisk %s" % name)
            for volume_xml in volumes_xml.xpath('OBJECT[@basetype="volumes"]'):
                volume_name = volume_xml.xpath(
                    'PROPERTY[@name="volume-name"]/text()'
                )[0]
                user_size = int(
                    volume_xml.xpath(
                        'PROPERTY[@name="size-numeric"]/text()'
                    )[0]
                )
                serial = volume_xml.xpath(
                    'PROPERTY[@name="serial-number"]/text()'
                )[0]
                volume_size = user_size * vdisk_raw_size / vdisk_size
                volumes.append((
                    unicode(volume_name),
                    unicode(serial),
                    volume_size,
                    unicode(disk_type),
                    disk_rpm,
                ))
    finally:
        ssh.close()
    vendor = system_xml.xpath('OBJECT/PROPERTY[@name="vendor-name"]/text()')[0]
    model = system_xml.xpath('OBJECT/PROPERTY[@name="product-id"]/text()')[0]
    brand = system_xml.xpath(
        'OBJECT/PROPERTY[@name="product-brand"]/text()'
    )[0]
    try:
        name = system_xml.xpath(
            'OBJECT/PROPERTY[@name="system-name"]/text()'
        )[0]
    except IndexError:
        name = None
    model_name = '%s %s %s' % (vendor, brand, model)
    try:
        sn = frus_xml.xpath(
            'OBJECT[PROPERTY[@name="name"]/text()="CHASSIS_MIDPLANE"]'
            '/PROPERTY[@name="serial-number"]/text()')[0]
    except IndexError:
        sn = None
    else:
        sn = unicode(sn)
    macs = network_xml.xpath('OBJECT/PROPERTY[@name="mac-address"]/text()')
    device_info = {
        'type': DeviceType.storage.raw,
        'model_name': model_name,
        'management_ip_addresses': [ip_address],
    }
    if sn not in SERIAL_BLACKLIST:
        device_info['serial_number'] = sn
    if macs:
        device_info['mac_addresses'] = [
            MACAddressField.normalize(unicode(mac)) for mac in macs
        ]
    shares = _handle_shares(volumes)
    if shares:
        device_info['disk_exports'] = shares
    return device_info


def scan_address(ip_address, **kwargs):
    if kwargs.get('http_family') not in ('WindRiver-WebServer',):
        raise NoMatchError("It's not a HP MSA Storage.")
    if 'nx-os' in (kwargs.get('snmp_name', '') or '').lower():
        raise NoMatchError("Incompatible Nexus found.")
    user = SETTINGS.get('user')
    password = SETTINGS.get('password')
    messages = []
    result = get_base_result_template('ssh_hp_msa', messages)
    if not user or not password:
        raise NotConfiguredError(
            'Not configured. Set SSH_MSA_USER and SSH_MSA_PASSWORD in '
            'your configuration file.',
        )
    result.update({
        'status': 'success',
        'device': _ssh_hp_msa(ip_address, user, password),
    })
    return result
