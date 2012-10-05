#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import ssh as paramiko
import collections
import logging

from django.conf import settings

from ralph.util import network, Eth, plugin, parse
from ralph.discovery.models import (Device, DeviceType, ComponentModel, Storage,
                                    Processor, ComponentType, Memory, IPAddress,
                                    DiskShare, DiskShareMount)
from ralph.discovery import hardware


XEN_USER = settings.XEN_USER
XEN_PASSWORD = settings.XEN_PASSWORD
SAVE_PRIORITY = 20

logger = logging.getLogger(__name__)


class Error(Exception):
    pass


def _connect_ssh(ip):
    return network.connect_ssh(ip, XEN_USER, XEN_PASSWORD)


def _ssh_lines(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    for line in stdout.readlines():
        yield line


def get_macs(ssh):
    """Get a dict of sets of macs of all the virtual machines."""

    macs = collections.defaultdict(set)
    label = ''
    for line in _ssh_lines(ssh, 'sudo xe vif-list params=vm-name-label,MAC'):
        line = line.strip()
        if not line:
            continue
        if line.startswith('vm-name-label'):
            label = line.split(':', 1)[1].strip()
        if label.startswith('Transfer VM for'):
            continue
        if line.startswith('MAC'):
            mac = line.split(':', 1)[1].strip()
            macs[label].add(mac)
    return macs


def get_disks(ssh):
    """Get a dict of lists of disks of virtual machines."""

    stdin, stdout, stderr = ssh.exec_command('sudo xe vm-disk-list '
            'vdi-params=sr-uuid,uuid,virtual-size '
            'vbd-params=vm-name-label,type,device '
            '--multiple')
    disks = collections.defaultdict(list)
    vm = None
    sr_uuid = None
    device = None
    type_ = None
    device = None
    size = None
    uuid = None
    for line in  stdout:
        if not line.strip():
            continue
        key, value = (x.strip() for x in line.split(':', 1))
        if key.startswith('vm-name-label '):
            vm = value
        elif key.startswith('sr-uuid '):
            sr_uuid = value
        elif key.startswith('type '):
            type_ = value
        elif key.startswith('device '):
            device = value
        elif key.startswith('uuid '):
            uuid = value
        elif key.startswith('virtual-size '):
            if type_ in {'Disk'}:
                disks[vm].append((uuid, sr_uuid, int(int(value)/1024), device))
    return disks


def get_srs(ssh):
    """Get a dict of disk SRs on the hypervisor."""

    stdin, stdout, stderr = ssh.exec_command('sudo xe sr-list '
            'params=uuid,physical-size,type')
    srs = {}
    size = None
    uuid = None
    for line in stdout:
        if not line.strip():
            continue
        key, value = (x.strip() for x in line.split(':', 1))
        if key.startswith('uuid '):
            uuid = value
        elif key.startswith('physical-size '):
            size = int(int(value)/1024)
        elif key.startswith('type '):
            if value in {'lvm'} and size > 0:
                srs[uuid] = size
    return srs


def get_running_vms(ssh):
    """Get a set of virtual machines running on the host."""

    stdin, stdout, stderr = ssh.exec_command('sudo xe vm-list '
            'params=uuid,name-label,power-state,VCPUs-number,memory-actual')
    data = stdout.read()
    vms = set()
    for vm_data in data.split('\n\n'):
        info = parse.pairs(lines=[
            line.replace('( RO)',
                         '').replace('( RW)',
                         '').replace('(MRO)',
                         '').strip()
            for line in vm_data.splitlines()])
        if not info:
            continue
        label = info['name-label']
        if (label.startswith('Transfer VM for') or
            label.startswith('Control domain on host:')):
            # Skip the helper virtual machines
            continue
        power = info['power-state']
        if power not in {'running'}:
            # Only include the running virtual machines
            continue
        cores = int(info['VCPUs-number'])
        memory = int(int(info['memory-actual'])/1024)
        uuid = info['uuid']
        vms.add((label, uuid, cores, memory))
    return vms


def run_ssh_xen(ipaddr, parent):
    ssh = _connect_ssh(ipaddr.address)
    try:
        vms = get_running_vms(ssh)
        macs = get_macs(ssh)
        disks = get_disks(ssh)
        shares = hardware.get_disk_shares(ssh)
    finally:
        ssh.close()

    for dev in parent.child_set.exclude(
            sn__in=[vm_uuid for (vm_name, vm_uuid, vm_cores, vm_memory) in vms]
        ):
        dev.deleted = True
        dev.save()
    for vm_name, vm_uuid, vm_cores, vm_memory in vms:
        ethernets = [Eth('vif %d' % i, mac, 0) for
                     i, mac in enumerate(macs.get(vm_name, []))]
        dev = Device.create(ethernets=ethernets, parent=parent, sn=vm_uuid,
                model_type=DeviceType.virtual_server,
                model_name='XEN Virtual Server', priority=SAVE_PRIORITY)
        dev.name = vm_name
        dev.save(priority=SAVE_PRIORITY)
        cpu_model, cpu_model_created = ComponentModel.concurrent_get_or_create(
            speed=0, type=ComponentType.processor.id, family='XEN Virtual',
            cores=0)
        if cpu_model_created:
            cpu_model.name = 'XEN Virtual CPU'
            cpu_model.save()
        for i in xrange(vm_cores):
            cpu, created = Processor.concurrent_get_or_create(device=dev,
                                                              index=i + 1)
            if created:
                cpu.label = 'CPU %d' % i
                cpu.model = cpu_model
                cpu.family = 'XEN Virtual'
                cpu.save()
        for cpu in dev.processor_set.filter(index__gt=vm_cores+1):
            cpu.delete()
        mem_model, mem_model_created = ComponentModel.concurrent_get_or_create(
            speed=0, type=ComponentType.memory.id, family='XEN Virtual',
            cores=0, size=0)
        if mem_model_created:
            mem_model.name = 'XEN Virtual Memory'
            mem_model.save()
        memory, created = Memory.concurrent_get_or_create(device=dev, index=1)
        memory.size = vm_memory
        memory.model = mem_model
        memory.label = 'XEN Memory'
        memory.save()
        for mem in dev.memory_set.filter(index__gt=1):
            mem.delete()
        disk_model, created = ComponentModel.concurrent_get_or_create(
                type=ComponentType.disk.id, family='XEN virtual disk')
        if created:
            disk_model.name = 'XEN virtual disk'
            disk_model.save()
        vm_disks = disks.get(vm_name, [])
        wwns = []
        for uuid, sr_uuid, size, device in vm_disks:
            wwn, mount_size = shares.get('VHD-%s' % sr_uuid, (None, None))
            if wwn:
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
                mount.size = mount_size
                mount.volume = device
                mount.save()
            else:
                storage, created = Storage.concurrent_get_or_create(
                    device=dev, mount_point=device, sn=uuid)
                storage.size = size
                storage.model = disk_model
                storage.label = device
                storage.save()
        for disk in dev.storage_set.exclude(sn__in={
            uuid for uuid, x , y , z in vm_disks
        }):
            disk.delete()
        for ds in dev.disksharemount_set.filter(
                server=parent).exclude(share__wwn__in=wwns):
            ds.delete()
        for ds in dev.disksharemount_set.filter(
                is_virtual=True).exclude(share__wwn__in=wwns):
            ds.delete()
    return ', '.join(vm_name for (vm_name, vm_uuid, vm_cores, vm_memory) in vms)


@plugin.register(chain='discovery', requires=['ping', 'snmp'])
def ssh_xen(**kwargs):
    ip = str(kwargs['ip'])
    if XEN_USER is None:
        return False, 'no auth.', kwargs
    if 'nx-os' in kwargs.get('snmp_name', '').lower():
        return False, 'incompatible Nexus found.', kwargs
    if 'xen' not in kwargs.get('snmp_name', ''):
        return False, 'no match.', kwargs
    if not network.check_tcp_port(ip, 22):
        return False, 'closed.', kwargs
    ipaddr = IPAddress.objects.get(address=ip)
    dev = ipaddr.device
    if dev is None:
        return False, 'no device.', kwargs
    try:
        name = run_ssh_xen(ipaddr, dev)
    except (network.Error, Error) as e:
        return False, str(e), kwargs
    except paramiko.SSHException as e:
        return False, str(e), kwargs
    except Error as e:
        return False, str(e), kwargs
    return True, name, kwargs

