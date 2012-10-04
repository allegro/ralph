#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""SSH-based disco for Proxmox hosts."""


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import ssh as paramiko
import logging
import json

from django.conf import settings
from lck.django.common import nested_commit_on_success
from lxml import etree as ET

from ralph.util import network
from ralph.util import plugin, Eth
from ralph.discovery.models import (DeviceType, Device, IPAddress, Software,
        DiskShare, DiskShareMount, ComponentModel, Processor, ComponentType,
        Storage)
from ralph.discovery.hardware import get_disk_shares


logger = logging.getLogger(__name__)


class Error(Exception):
    pass

class NotProxmoxError(Error):
    pass


def _connect_ssh(ip, username='root', password=''):
    return network.connect_ssh(ip, 'root', settings.SSH_PASSWORD)


def _get_local_disk_size(ssh, disk):
    """Return the size of a disk image file, in bytes"""

    path = os.path.join('/var/lib/vz/images', disk)
    stdin, stdout, stderr = ssh.exec_command("du -m '%s'" % path)
    line = stdout.read().strip()
    if not line:
        return 0
    size = int(line.split(None, 1)[0])
    return size


def _add_virtual_machine(ssh, vmid, parent, master, storages):
    stdin, stdout, stderr = ssh.exec_command(
            "cat /etc/qemu-server/%d.conf" % vmid)
    lines = stdout.readlines()
    if not lines:
        # Proxmox 2 uses a different directory structure
        stdin, stdout, stderr = ssh.exec_command(
            "cat /etc/pve/nodes/*/qemu-server/%d.conf" % vmid)
        lines = stdout.readlines()
    disks = {}
    lan_model = None
    name = 'unknown'
    for line in lines:
        line = line.strip()
        key, value = line.split(':', 1)
        if key.startswith('vlan'):
            lan_model, lan_mac = value.split('=', 1)
        elif key.startswith('net'):
            lan_model, lan_mac = value.split('=', 1)
            if ',' in lan_mac:
                lan_mac = lan_mac.split(',', 1)[0]
        elif key == 'name':
            name = value.strip()
        elif key == 'sockets':
            cpu_count = int(value.strip())
        elif key.startswith('ide') or key.startswith('virtio'):
            disks[key] = value.strip()
    if lan_model is None:
        return None
    dev = Device.create(
            model_name='Proxmox qemu kvm',
            model_type=DeviceType.virtual_server,
            ethernets=[Eth(label=lan_model, mac=lan_mac, speed=0)],
            parent=parent,
            management=master,
            name=name
        )
    wwns = []
    for slot, disk in disks.iteritems():
        params = {}
        if ',' in disk:
            disk, rawparams = disk.split(',', 1)
            for kv in rawparams.split(','):
                if not kv.strip():
                    continue
                k, v = kv.split('=', 1)
                params[k] = v.strip()
        if ':' in disk:
            vg, lv = disk.split(':', 1)
        else:
            vg = ''
            lv = disk
        if vg == 'local':
            size = _get_local_disk_size(ssh, lv)
            if not size > 0:
                continue
            model, created = ComponentModel.concurrent_get_or_create(
                type=ComponentType.disk.id, family='QEMU disk image')
            if created:
                model.save()
            storage, created = Storage.concurrent_get_or_create(
                device=dev, mount_point=lv)
            storage.size = size
            storage.model = model
            storage.label = slot
            storage.save()
            continue
        if vg in ('', 'local', 'pve-local'):
            continue
        vol = '%s:%s' % (vg, lv)
        try:
            wwn, size = storages[lv]
        except KeyError:
            logger.warning('Volume %r does not exist.' % lv)
            continue
        try:
            share = DiskShare.objects.get(wwn=wwn)
            wwns.append(wwn)
        except DiskShare.DoesNotExist:
            logger.warning('A share with WWN %r does not exist.' % wwn)
            continue
        mount, created = DiskShareMount.concurrent_get_or_create(
                share=share, device=dev)
        mount.is_virtual = True
        mount.server = parent
        mount.size = size
        mount.volume = vol
        mount.save()
    for ds in dev.disksharemount_set.filter(
            server=parent).exclude(share__wwn__in=wwns):
        ds.delete()
    for ds in dev.disksharemount_set.filter(
            is_virtual=True).exclude(share__wwn__in=wwns):
        ds.delete()

    cpu_model, cpu_model_created = ComponentModel.concurrent_get_or_create(
        speed=0, type=ComponentType.processor.id, family='QEMU Virtual',
        cores=0)
    if cpu_model_created:
        cpu_model.name = 'QEMU Virtual CPU version 0.12.4'
        cpu_model.save()
    for i in range(cpu_count):
        cpu, cpu_created = Processor.concurrent_get_or_create(device=dev,
                                                              index=i+1)
        if cpu_created:
            cpu.label = 'CPU {}'.format(i + 1)
            cpu.model = cpu_model
            cpu.family = 'QEMU Virtual'
            cpu.save()

    dev.save(update_last_seen=True)
    return dev

def _add_virtual_machines(ssh, parent, master):
    storages = get_disk_shares(ssh)
    stdin, stdout, stderr = ssh.exec_command("qm list")
    dev_ids = []
    for line in stdout:
        line = line.strip()
        if line.startswith('VMID'):
            continue
        vmid, name, status, mem, bootdisk, pid = (v.strip() for
                v in line.split())
        if status != 'running':
            continue
        vmid = int(vmid)
        dev = _add_virtual_machine(ssh, vmid, parent, master, storages)
        if dev is None:
            continue
        dev_ids.append(dev.id)
    for child in parent.child_set.exclude(id__in=dev_ids):
        logger.info('Deleting virtual server %r that no longer exists.' % child)
        child.deleted = True
        child.save()


def _get_master(ssh, ip, data=None):
    if data is None:
        stdin, stdout, stderr = ssh.exec_command("cat /etc/pve/cluster.cfg")
        data = stdout.read()
    if not data:
        stdin, stdout, stderr = ssh.exec_command("pvesh get /nodes")
        data = stdout.read()
        if data:
            nodes = json.loads(data)
            for node in nodes:
                node_name = node['node']
                stdin, stdout, stderr = ssh.exec_command(
                        'pvesh get "/nodes/%s/dns"' % node_name)
                dns = json.loads(stdout.read())
                ip = dns['dns1']
                break
    if not data:
        ipaddr, ip_created = IPAddress.concurrent_get_or_create(address=ip)
        ipaddr.save()
        return ipaddr
    nodes = {}
    current_node = None
    for line in data.splitlines():
        line = line.strip()
        if line.endswith('{'):
            current_node = line.replace('{', '').strip()
            nodes[current_node] = {}
        elif line.endswith('}'):
            current_node = None
        elif ':' in line and current_node:
            key, value = (v.strip() for v in line.split(':', 1))
            nodes[current_node][key] = value
    for node, pairs in nodes.iteritems():
        is_master = node.startswith('master')
        try:
            ip = pairs['IP']
        except KeyError:
            continue
        if is_master:
            ipaddr, ip_created = IPAddress.concurrent_get_or_create(address=ip)
            ipaddr.save()
            return ipaddr


def _add_cluster_member(ssh, ip):
    stdin, stdout, stderr = ssh.exec_command("ifconfig eth0 | head -n 1")
    mac = stdout.readline().split()[-1]

    dev = Device.create(ethernets=[Eth(label='eth0', mac=mac, speed=0)],
            model_name='Proxmox', model_type=DeviceType.unknown)

    Software.create(dev, 'proxmox', 'Proxmox', family='Virtualization').save()
    ipaddr, ip_created = IPAddress.concurrent_get_or_create(address=ip)
    ipaddr.is_management = False
    ipaddr.device = dev
    ipaddr.save()
    return dev


@nested_commit_on_success
def run_ssh_proxmox(ip):
    ssh = _connect_ssh(ip)
    try:
        for file_name in ('/etc/pve/cluster.cfg', '/etc/pve/cluster.conf',
                          '/etc/pve/storage.cfg'):
            stdin, stdout, stderr = ssh.exec_command('cat "%s"' % file_name)
            data = stdout.read()
            if data != '':
                break
        else:
            raise NotProxmoxError('this is not a PROXMOX server.')
        master = _get_master(ssh, ip)
        member = _add_cluster_member(ssh, ip)
        _add_virtual_machines(ssh, member, master)
    finally:
        ssh.close()
    return member.sn or member.name

@plugin.register(chain='discovery', requires=['ping', 'http'])
def ssh_proxmox(**kwargs):
    if 'nx-os' in kwargs.get('snmp_name', '').lower():
        return False, 'incompatible Nexus found.', kwargs
    ip = str(kwargs['ip'])
    if kwargs.get('http_family') not in ('Proxmox',):
        return False, 'no match.', kwargs
    if not network.check_tcp_port(ip, 22):
        return False, 'closed.', kwargs
    try:
        name = run_ssh_proxmox(ip)
    except (network.Error, Error) as e:
        return False, str(e), kwargs
    except paramiko.SSHException as e:
        return False, str(e), kwargs
    except Error as e:
        return False, str(e), kwargs
    return True, name, kwargs

