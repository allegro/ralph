# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import time
import ssh as paramiko

from lck.django.common import nested_commit_on_success
from lxml import etree as ET

from ralph.util import Eth
from ralph.discovery.models import (DeviceType, Device, IPAddress,
                                    DiskShare, ComponentModel, ComponentType)
from ralph.discovery.hardware import normalize_wwn

class Error(Exception):
    pass

class ConsoleError(Error):
    pass


class HPSSHClient(paramiko.SSHClient):
    """SSHClient modified for Cisco's broken ssh console."""

    def __init__(self, *args, **kwargs):
        super(HPSSHClient, self).__init__(*args, **kwargs)
        self.set_log_channel('critical_only')

    def _auth(self, username, password, pkey, key_filenames, allow_agent, look_for_keys):
        self._transport.auth_password(username, password)
        self._hp_chan = self._transport.open_session()
        self._hp_chan.invoke_shell()
        chunk = self._hp_chan.recv(1024)
        self._hp_chan.sendall('\r\n')
        time.sleep(0.25)
        chunk = self._hp_chan.recv(1024)
        if not chunk.endswith('# '):
            raise ConsoleError('Expected system prompt, got %r.' % chunk)

    def hp_command(self, command):
        # XXX Work around random characters appearing at the beginning of the command.
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


def run(ssh, ip):
    try:
        ssh.hp_command("set cli-parameters api pager off")
        system_xml = ssh.hp_command("show system")
        network_xml = ssh.hp_command("show network-parameters")
        frus_xml = ssh.hp_command("show frus")
        vdisks_xml = ssh.hp_command("show vdisks")

        volumes = []
        for vdisk_xml in vdisks_xml.xpath('OBJECT[@basetype="virtual-disks"]'):
            vdisk_size = int(vdisk_xml.xpath('PROPERTY[@name="size-numeric"]/text()')[0])
            name = vdisk_xml.xpath('PROPERTY[@name="name"]/text()')[0]
            vdisk_raw_size = 0
            disks_xml = ssh.hp_command("show disks vdisk %s" % name)
            disk_type = 'unknown'
            disk_rpm = 0
            for disk_xml in disks_xml.xpath('OBJECT[@basetype="drives"]'):
                disk_size = int(disk_xml.xpath('PROPERTY[@name="size-numeric"]/text()')[0])
                try:
                    disk_type = disk_xml.xpath('PROPERTY[@name="type"]/text()')[0]
                except IndexError:
                    pass
                try:
                    disk_rpm = int(disk_xml.xpath('PROPERTY[@name="rpm"]/text()')[0])
                except IndexError:
                    pass
                vdisk_raw_size += disk_size
            volumes_xml = ssh.hp_command("show volumes vdisk %s" % name)
            for volume_xml in volumes_xml.xpath('OBJECT[@basetype="volumes"]'):
                volume_name = volume_xml.xpath('PROPERTY[@name="volume-name"]/text()')[0]
                user_size = int(volume_xml.xpath('PROPERTY[@name="size-numeric"]/text()')[0])
                serial = volume_xml.xpath('PROPERTY[@name="serial-number"]/text()')[0]
                volume_size = user_size * vdisk_raw_size / vdisk_size
                volumes.append((volume_name, serial, volume_size, disk_type, disk_rpm))
    finally:
        ssh.close()
    vendor = system_xml.xpath('OBJECT/PROPERTY[@name="vendor-name"]/text()')[0]
    model = system_xml.xpath('OBJECT/PROPERTY[@name="product-id"]/text()')[0]
    brand = system_xml.xpath('OBJECT/PROPERTY[@name="product-brand"]/text()')[0]
    try:
        name = system_xml.xpath(
                'OBJECT/PROPERTY[@name="system-name"]/text()')[0]
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
    dev = _save_device(ip, name, model_name, sn, macs)
    _save_shares(dev, volumes)
    return dev.name

@nested_commit_on_success
def _save_shares(dev, volumes):
    wwns = []
    for (label, serial, size, type, speed) in volumes:
        wwn = normalize_wwn(serial)
        wwns.append(wwn)
        model, created = ComponentModel.concurrent_get_or_create(
            name='MSA %s disk share' % type, type=ComponentType.share.id,
            family=type, speed=speed)
        share, created = DiskShare.concurrent_get_or_create(wwn=wwn, device=dev)
        share.model = model
        share.label = label
        share.size = size * 512 / 1024 / 1024
        share.snapshot_size = 0
        share.save()
    dev.diskshare_set.exclude(wwn__in=wwns).delete()

@nested_commit_on_success
def _save_device(ip, name, model_name, sn, macs):
    ethernets = [Eth(mac=mac, label='MAC', speed=0) for mac in macs]
    dev = Device.create(sn=sn, model_name=model_name, ethernets=ethernets,
                        model_type=DeviceType.storage, name=name)
    ipaddr, ip_created = IPAddress.concurrent_get_or_create(address=ip)
    ipaddr.device = dev
    ipaddr.is_management = True
    ipaddr.save()
    dev.management = ipaddr
    dev.save()
    return dev
