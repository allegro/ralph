#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import paramiko
import re

from django.conf import settings
from lck.django.common import nested_commit_on_success

from ralph.util import network, Eth
from ralph.util import plugin
from ralph.discovery import guessmodel
from ralph.discovery.hardware import normalize_wwn
from ralph.discovery.models import (
    Device, DeviceType, DiskShareMount, DiskShare,
    ComponentType, ComponentModel, Storage,
    Processor, Memory, IPAddress, OperatingSystem
)


AIX_USER = settings.AIX_USER
AIX_PASSWORD = settings.AIX_PASSWORD
AIX_KEY = settings.AIX_KEY

MODELS = {
    'IBM,9131-52A': 'IBM P5 520',
    'IBM,8203-E4A': 'IBM P6 520',
    'IBM,8233-E8B': 'IBM Power 750 Express',
}

SAVE_PRIORITY = 4


class Error(Exception):
    pass


def _connect_ssh(ip):
    return network.connect_ssh(ip, AIX_USER, AIX_PASSWORD, key=AIX_KEY)


def _ssh_lines(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    for line in stdout.readlines():
        yield line


@nested_commit_on_success
def run_ssh_aix(ip):
    ssh = _connect_ssh(ip)
    try:
        ethernets = []
        for model_line in _ssh_lines(ssh, 'lsattr -El sys0 | grep ^modelname'):
            machine_model = model_line.split(None, 2)[1]
            break
        for mac_line in _ssh_lines(ssh, 'netstat -ia | grep link'):
            interface, mtu, net, mac, rest = mac_line.split(None, 4)
            if '.' not in mac:
                continue
            octets = mac.split('.')
            mac = ''.join('%02x' % int(o, 16) for o in octets).upper()
            ethernets.append(Eth(label=interface, mac=mac, speed=0))
        disks = {}
        os_storage_size = 0
        for disk_line in _ssh_lines(ssh, 'lsdev -c disk'):
            disk, rest = disk_line.split(None, 1)
            wwn = None
            model = None
            for line in _ssh_lines(ssh, 'lscfg -vl %s' % disk):
                if 'hdisk' in line:
                    match = re.search(r'\(([0-9]+) MB\)', line)
                    if match:
                        os_storage_size += int(match.group(1))
                elif 'Serial Number...' in line:
                    label, sn = line.split('.', 1)
                    sn = sn.strip('. \n')
                elif 'Machine Type and Model.' in line:
                    label, model = line.split('.', 1)
                    model = model.strip('. \n')
            disks[disk] = (model, sn)
        os_version = ''
        for line in _ssh_lines(ssh, 'oslevel'):
            os_version = line.strip()
            break
        os_memory = 0
        for line in _ssh_lines(ssh, 'lsattr -El sys0 | grep ^realmem'):
            match = re.search(r'[0-9]+', line)
            if match:
                os_memory = int(int(match.group(0)) / 1024)
            break
        os_corescount = 0
        for line in _ssh_lines(ssh, 'lparstat -i|grep ^Active\ Phys'):
            match = re.search(r'[0-9]+', line)
            if match:
                os_corescount += int(match.group(0))
    finally:
        ssh.close()
    dev = Device.create(
        ethernets=ethernets, model_type=DeviceType.rack_server,
        model_name='%s AIX' % MODELS.get(machine_model, machine_model))
    ipaddr = IPAddress.objects.get(address=ip)
    ipaddr.device = dev
    ipaddr.save()
    wwns = []
    sns = []
    stors = []
    for disk, (model_name, sn) in disks.iteritems():
        if not sn:
            continue
        if model_name == 'VV':
            wwns.append(sn)
        else:
            stors.append((disk, model_name, sn))
            sns.append(sn)
    for mount in dev.disksharemount_set.exclude(share__wwn__in=wwns):
        mount.delete()
    for stor in dev.storage_set.exclude(sn__in=sns):
        stor.delete()
    for wwn in wwns:
        try:
            share = DiskShare.objects.get(wwn=wwn)
        except DiskShare.DoesNotExist:
            continue
        wwn = normalize_wwn(sn[-4:] + sn[:-4])
        mount, created = DiskShareMount.concurrent_get_or_create(
            share=share, device=dev, defaults={'is_virtual': False})
        mount.volume = disk
        mount.save(priority=SAVE_PRIORITY)
    for disk, model_name, sn in stors:
        # FIXME: storage with no size
        model, c = ComponentModel.create(
            ComponentType.disk,
            family=model_name,
            priority=SAVE_PRIORITY,
        )
        stor, created = Storage.concurrent_get_or_create(
            device=dev,
            sn=sn,
            mount_point=None,
        )
        stor.model = model
        stor.label = disk
        stor.save(priority=SAVE_PRIORITY)
    # FIXME: memory with no size
    mem, created = Memory.concurrent_get_or_create(device=dev, index=0)
    mem.label = 'Memory'
    mem.model, c = ComponentModel.create(
        ComponentType.memory,
        family='pSeries',
        priority=SAVE_PRIORITY,
    )
    mem.save(priority=SAVE_PRIORITY)
    # FIXME: CPUs without info
    cpu, created = Processor.concurrent_get_or_create(device=dev, index=0)
    cpu.label = 'CPU'
    cpu.model, c = ComponentModel.create(
        ComponentType.processor,
        family='pSeries',
        name='pSeries CPU',
        priority=SAVE_PRIORITY,
    )
    cpu.save(priority=SAVE_PRIORITY)
    OperatingSystem.create(dev=dev,
                           os_name='AIX',
                           version=os_version,
                           family='AIX',
                           memory=os_memory or None,
                           cores_count=os_corescount or None,
                           storage=os_storage_size or None,
                           priority=SAVE_PRIORITY
                           )
    return machine_model


@plugin.register(chain='discovery', requires=['ping'])
def ssh_aix(**kwargs):
    if 'nx-os' in kwargs.get('snmp_name', '').lower():
        return False, 'incompatible Nexus found.', kwargs
    ip = str(kwargs['ip'])
    if AIX_USER is None:
        return False, 'no auth.', kwargs
    kwargs['guessmodel'] = gvendor, gmodel = guessmodel.guessmodel(**kwargs)
    if gvendor != 'IBM':
        return False, 'no match: %s %s' % (gvendor, gmodel), kwargs
    snmp_name = kwargs.get('snmp_name', '')
    if snmp_name and not snmp_name.startswith('IBM PowerPC'):
        return False, 'no match.', kwargs
    if not network.check_tcp_port(ip, 22):
        return False, 'closed.', kwargs
    try:
        name = run_ssh_aix(ip)
    except (network.Error, Error) as e:
        return False, str(e), kwargs
    except paramiko.SSHException as e:
        return False, str(e), kwargs
    except Error as e:
        return False, str(e), kwargs
    return True, name, kwargs
