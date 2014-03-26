#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A discovery plugin for ganeti virtual server hypervisors.

This plugin tries to connect through SSH to the server and execute Ganeti-
-specific commands to get information about its cluster master, and all
the virtual servers running on it. I also sets all the virtual servers that
were there but are not anymore to deleted.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings
from lck.django.common.models import MACAddressField
from django.db.models import Q
import paramiko

from ralph.discovery.models import Device, DeviceType, IPAddress
from ralph.util import Eth, network, plugin


SAVE_PRIORITY = 50


class Error(Exception):
    pass


def _connect_ssh(ip):
    if not settings.SSH_PASSWORD:
        raise Error('no password defined')
    return network.connect_ssh(
        ip,
        settings.SSH_USER or 'root',
        settings.SSH_PASSWORD,
    )


def get_device(hostname, default=None):
    qs = Device.objects.filter(
        Q(name=hostname) |
        Q(ipaddress__hostname=hostname)
    ).distinct()
    for device in qs[:1]:
        return device
    return default


def get_master_hostname(ssh):
    stdin, stdout, stderr = ssh.exec_command('/usr/sbin/gnt-cluster getmaster')
    master = stdout.read().strip()
    if not master:
        raise Error('not a ganeti node.')
    return master


def get_instances(ssh):
    stdin, stdout, stderr = ssh.exec_command(
        '/usr/sbin/gnt-instance list -o name,pnode,snodes,ip,mac --no-headers',
    )
    for line in stdout:
        line = line.strip()
        if not line:
            continue
        hostname, primary_node, secondary_nodes, ip, mac = line.split()
        if ip == '-':
            ip = None
        mac = MACAddressField.normalize(mac)
        yield hostname, primary_node, ip, mac


def run_ssh_ganeti(ip):
    ssh = _connect_ssh(ip)
    master_hostname = get_master_hostname(ssh)
    try:
        master_ip = IPAddress.objects.get(
            Q(hostname=master_hostname) |
            Q(address=master_hostname)
        )
    except IPAddress.DoesNotExist:
        raise Error('unknown master hostname %r' % master_hostname)
    if master_ip.address != ip:
        raise Error('not a cluster master.')
    existing_macs = set()
    for hostname, primary_node, address, mac in get_instances(ssh):
        parent = get_device(primary_node)
        existing_macs.add(mac)
        dev = Device.create(
            ethernets=[Eth(label='eth0', mac=mac, speed=0)],
            parent=parent,
            management=master_ip,
            model_name='Ganeti',
            model_type=DeviceType.virtual_server,
            family='Virtualization',
            priority=SAVE_PRIORITY,
        )
        dev.name = hostname
        dev.save(priority=SAVE_PRIORITY)
        if address:
            ip_address, created = IPAddress.concurrent_get_or_create(
                address=address,
            )
            ip_address.device = dev
            ip_address.save()
    for dev in Device.objects.filter(
            management=master_ip,
            model__name='Ganeti',
    ).exclude(
            ethernet__mac__in=existing_macs,
    ):
        dev.deleted = True
        dev.save(priority=SAVE_PRIORITY)
    return master_hostname


@plugin.register(chain='discovery', requires=['ping', 'snmp'])
def ssh_ganeti(**kwargs):
    if 'nx-os' in kwargs.get('snmp_name', '').lower():
        return False, 'incompatible Nexus found.', kwargs
    ip = str(kwargs['ip'])
    if not network.check_tcp_port(ip, 22):
        return False, 'port 22 closed.', kwargs
    try:
        name = run_ssh_ganeti(ip)
    except (network.Error, Error, paramiko.SSHException) as e:
        return False, str(e), kwargs
    return True, name, kwargs
