#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import ssh as paramiko

from django.conf import settings

from ralph.util import network, Eth, plugin, parse
from ralph.discovery.models import (Device, DeviceType, ComponentModel,
                                    Processor, ComponentType, Memory, IPAddress)


XEN_USER = settings.XEN_USER
XEN_PASSWORD = settings.XEN_PASSWORD
SAVE_PRIORITY = 20


class Error(Exception):
    pass


def _connect_ssh(ip):
    return network.connect_ssh(ip, XEN_USER, XEN_PASSWORD)


def _ssh_lines(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    for line in stdout.readlines():
        yield line

def get_macs(ssh):
    macs = {}
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
            macs.setdefault(label, set()).add(mac)
    return macs

def get_running_vms(ssh):
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

