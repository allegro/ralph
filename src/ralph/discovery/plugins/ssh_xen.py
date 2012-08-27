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
from ralph.discovery.models import IPAddress
from ralph.discovery.models import Device, DeviceType


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
    vms = set()
    label = ''
    uuid = ''
    for line in _ssh_lines(ssh,
                       'sudo xe vm-list params=uuid,name-label,power-state'):
        line = line.strip()
        if not line:
            continue
        if line.startswith('name-label'):
            label = line.split(':', 1)[1].strip()
        if (label.startswith('Transfer VM for') or
            label.startswith('Control domain on host:')):
            continue
        if line.startswith('uuid'):
            uuid = line.split(':', 1)[1].strip()
        if line.startswith('power-state'):
            state = line.split(':', 1)[1].strip()
            if state == 'running':
                vms.add((label, uuid))
    return vms


def run_ssh_xen(ipaddr, parent):
    ssh = _connect_ssh(ipaddr.address)
    try:
        vms = get_running_vms(ssh)
        macs = get_macs(ssh)
    finally:
        ssh.close()

    for dev in parent.child_set.exclude(
            sn__in=[vm_uuid for (vm_name, vm_uuid) in vms]
        ):
        dev.deleted = True
        dev.save()
    for vm_name, vm_uuid in vms:
        ethernets = [Eth('vif %d' % i, mac, 0) for
                     i, mac in enumerate(macs.get(vm_name, []))]
        dev = Device.create(ethernets=ethernets, parent=parent, sn=vm_uuid,
                model_type=DeviceType.virtual_server,
                model_name='XEN Virtual Server', priority=SAVE_PRIORITY)
        dev.name = vm_name
        dev.save(priority=SAVE_PRIORITY)
    return ', '.join(vm_name for (vm_name, vm_uuid) in vms)


@plugin.register(chain='discovery', requires=['ping', 'snmp'])
def ssh_xen(**kwargs):
    ip = str(kwargs['ip'])
    if XEN_USER is None:
        return False, 'no auth.', kwargs
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

