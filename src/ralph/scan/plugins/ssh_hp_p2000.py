# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import time
import json
import paramiko

from lck.django.common.models import MACAddressField
from lxml import etree as ET
from django.conf import settings

from ralph.discovery.hardware import normalize_wwn
from ralph.discovery.models import SERIAL_BLACKLIST
from ralph.util import network
from ralph.scan.errors import (
    SSHConsoleError,
    NoMatchError,
    ConnectionError,
)
from ralph.scan.plugins import get_base_result_template


class HPSSHClient(paramiko.SSHClient):

    """SSHClient modified for Cisco's broken ssh console."""

    def __init__(self, *args, **kwargs):
        super(HPSSHClient, self).__init__(*args, **kwargs)
        self.set_log_channel('critical_only')

    def _auth(self, username, password, pkey, key_filenames, allow_agent,
              look_for_keys):
        self._transport.auth_password(username, password)
        self._hp_chan = self._transport.open_session()
        self._hp_chan.invoke_shell()
        chunk = self._hp_chan.recv(1024)
        self._hp_chan.sendall('\r\n')
        time.sleep(0.25)
        chunk = self._hp_chan.recv(1024)
        if not chunk.endswith('# '):
            raise SSHConsoleError('Expected system prompt, got %r.' % chunk)

    def hp_command(self, command):
        # XXX Work around random characters appearing at the beginning of
        # the command.
        self._hp_chan.sendall(b'\b')
        time.sleep(0.125)
        self._hp_chan.sendall(command)
        buffer = b'# '
        end = command[-32:]
        while not buffer.strip(b'\b ').endswith(end):
            chunk = self._hp_chan.recv(1024)
            buffer += chunk
        self._hp_chan.sendall(b'\r\n')
        buffer = [b'']
        while True:
            chunk = self._hp_chan.recv(1024)
            lines = chunk.split(b'\n')
            buffer[-1] += lines[0]
            buffer.extend(lines[1:])
            if buffer[-1].endswith(b'# '):
                break
        text = b''.join(line for line in buffer if not line.startswith(b'# '))
        return ET.fromstring(text.strip())


def run_storageworks(ssh, ip):
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
                    volume_name,
                    serial,
                    volume_size,
                    disk_type,
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
    macs = network_xml.xpath('OBJECT/PROPERTY[@name="mac-address"]/text()')
    shares = _shares(volumes)
    dev = _device(ip, name, model_name, sn, macs, shares)
    return dev


def _shares(volumes):
    shares = []
    for (label, serial, size, volume_type, speed) in volumes:
        wwn = normalize_wwn(serial)
        share = {
            'serial_number': str(wwn),
            'size': size * 512 / 1024 / 1024,
            'label': 'MSA %s disk share' % volume_type,
        }
        shares.append(share)
    return shares


def _device(ip, name, model_name, sn, macs, shares):
    device = {
        'management_ip_addresses': [ip],
        'hostname': name,
        'model_name': model_name,
        'mac_addresses': [
            MACAddressField.normalize(mac) for mac in macs
        ],
        'disk_exports': shares,
    }
    if sn not in SERIAL_BLACKLIST:
        device['serial_number'] = sn
    return device


SSH_P2000_USER = settings.SCAN_PLUGINS[__name__].get('ssh_user')
SSH_P2000_PASSWORD = settings.SCAN_PLUGINS[__name__].get('ssh_password')


def _connect_ssh(ip):
    return network.connect_ssh(ip, SSH_P2000_USER, SSH_P2000_PASSWORD,
                               client=HPSSHClient)


def _run_ssh_p2000(ip):
    ssh = _connect_ssh(ip)
    return run_storageworks(ssh, ip)


def scan_address(ip_address, **kwargs):
    snmp_name = kwargs.get('snmp_name', '') or ''
    if 'nx-os' in snmp_name.lower():
        raise NoMatchError("Incompatible Nexus found.")
    if 'StorageWorks' not in snmp_name:
        raise NoMatchError("No match")
    if not network.check_tcp_port(ip_address, 22):
        raise ConnectionError("Port 22 closed.")
    device = _run_ssh_p2000(ip_address)
    ret = {
        'status': 'success',
        'device': device,
    }
    tpl = get_base_result_template('ssh_hp_p2000')
    tpl.update(ret)
    return json.loads(json.dumps(tpl))  # to ensure its picklable
