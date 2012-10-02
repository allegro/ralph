#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import ssh as paramiko

from django.conf import settings
from lck.django.common import nested_commit_on_success

from ralph.util import network, Eth
from ralph.util import plugin
from ralph.discovery import guessmodel
from ralph.discovery.hardware import normalize_wwn
from ralph.discovery.models import (
    Device, DeviceType, DiskShareMount, DiskShare,
    ComponentType, ComponentModel, Storage,
    Processor, Memory, IPAddress
)


AIX_USER = settings.AIX_USER
AIX_PASSWORD = settings.AIX_PASSWORD
AIX_KEY = settings.AIX_KEY

MODELS = {
    'IBM,9131-52A': 'IBM P5 520',
    'IBM,8203-E4A': 'IBM P6 520',
    'IBM,8233-E8B': 'IBM Power 750 Express',
}



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
        for disk_line in _ssh_lines(ssh, 'lsdev -c disk'):
            disk, rest = disk_line.split(None, 1)
            wwn = None
            model = None
            for line in _ssh_lines(ssh, 'lscfg -vl %s' % disk):
                if 'Serial Number...' in line:
                    label, sn = line.split('.', 1)
                    sn = sn.strip('. \n')
                elif 'Machine Type and Model.' in line:
                    label, model = line.split('.', 1)
                    model = model.strip('. \n')
            disks[disk] = (model, sn)
    finally:
        ssh.close()
    dev = Device.create(
                ethernets=ethernets,
                model_type=DeviceType.rack_server,
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
                share=share, device=dev, is_virtual=False)
        mount.volume = disk
        mount.save()
    for disk, model_name, sn in stors:
        model, mcreated = ComponentModel.concurrent_get_or_create(
                type=ComponentType.disk.id, family=model_name, extra_hash='')
        model.name = model_name
        model.save()
        stor, created = Storage.concurrent_get_or_create(device=dev, sn=sn)
        stor.model = model
        stor.label = disk
        stor.save()


    mem, created = Memory.concurrent_get_or_create(device=dev, index=0)
    mem.label = 'Memory'
    mem.model, c = ComponentModel.concurrent_get_or_create( size=0, speed=0,
            type=ComponentType.memory.id, family='pSeries', extra_hash='')
    mem.model.name = 'pSeries Memory'
    mem.model.save()
    mem.save()
    cpu, created = Processor.concurrent_get_or_create(device=dev, index=0)
    cpu.label = 'CPU'
    cpu.model, c = ComponentModel.concurrent_get_or_create(speed=0, cores=0,
            type=ComponentType.processor.id, extra_hash='', family='pSeries CPU')
    cpu.model.name = 'pSeries CPU'
    cpu.model.save()
    cpu.save()

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

