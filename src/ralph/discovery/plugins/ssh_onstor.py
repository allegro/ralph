#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import collections
import paramiko

from django.conf import settings
from lck.django.common import nested_commit_on_success

from ralph.util import network
from ralph.util import plugin
from ralph.util import parse
from ralph.discovery.models import (DeviceType, DeviceModel, Device, IPAddress,
                                    DiskShare, DiskShareMount)
from ralph.discovery.models_history import DiscoveryWarning


SSH_ONSTOR_USER = settings.SSH_ONSTOR_USER
SSH_ONSTOR_PASSWORD = settings.SSH_ONSTOR_PASSWORD


class Error(Exception):
    pass


class SkipError(Error):
    pass


def _connect_ssh(ip):
    return network.connect_ssh(ip, SSH_ONSTOR_USER, SSH_ONSTOR_PASSWORD)


def _save_shares(dev, luns, mounts):
    wwns = []
    for lun, volume in luns.iteritems():
        rest, wwn_end = lun.rsplit('_', 1)
        try:
            share = DiskShare.objects.get(wwn__endswith=wwn_end)
        except DiskShare.DoesNotExist:
            continue
        wwns.append(share.wwn)
        clients = mounts.get(volume, [])
        for client in clients:
            ipaddr, ip_created = IPAddress.concurrent_get_or_create(
                address=client,
            )
            mount, created = DiskShareMount.concurrent_get_or_create(
                device=ipaddr.device,
                share=share,
                defaults={
                    'address': ipaddr,
                    'server': dev,
                }
            )
            if not created:
                mount.address = ipaddr
                mount.server = dev
            mount.volume = volume
            mount.save(update_last_seen=True)
        if not clients:
            mount, created = DiskShareMount.concurrent_get_or_create(
                device=None,
                share=share,
                defaults={
                    'address': None,
                    'server': dev,
                }
            )
            if not created:
                mount.address = None
                mount.server = dev
            mount.volume = volume
            mount.save(update_last_seen=True)
    for mount in DiskShareMount.objects.filter(
        server=dev
    ).exclude(
        share__wwn__in=wwns
    ):
        mount.delete()


@nested_commit_on_success
def _save_device(ip, name, model_name, sn, mac):
    model, model_created = DeviceModel.concurrent_get_or_create(
        name='Onstor %s' % model_name,
        defaults={
            'type': DeviceType.storage.id,
        },
    )
    dev = Device.create(sn=sn, model=model)
    dev.save()
    ipaddr, ip_created = IPAddress.concurrent_get_or_create(address=ip)
    ipaddr.device = dev
    ipaddr.is_management = True
    ipaddr.save(update_last_seen=True)
    dev.management = ipaddr
    dev.save(update_last_seen=True)
    return dev


def _command(channel, command):
    buffer = ''
    channel.sendall('\r\n')
    while not buffer.endswith('> '):
        buffer += channel.recv(1024)
    channel.sendall(command)
    buffer = ''
    while command not in buffer:
        buffer += channel.recv(1024)
    channel.sendall('\r\n')
    buffer = ['']
    while not buffer[-1].endswith('> '):
        chunk = channel.recv(1024)
        lines = chunk.split('\n')
        buffer[-1] += lines[0]
        buffer.extend(lines[1:])
    return buffer[1:-1]


def _run_ssh_onstor(ip):
    ssh = _connect_ssh(ip)
    try:
        stdin, stdout, stderr = ssh.exec_command("system show summary")
        pairs = parse.pairs(lines=stdout.readlines())
        name = pairs['Name']
        model_name = pairs['--------']['Model number']
        sn = pairs['--------']['System serial number']
        mac = pairs['--------']['MAC addr'].upper().replace(':', '')

        dev = _save_device(ip, name, model_name, sn, mac)
        first_ip = dev.ipaddress_set.order_by('address')[0].address
        if ip != first_ip:
            raise SkipError('multiple addresses (will check %s).' % first_ip)

        stdin, stdout, stderr = ssh.exec_command("lun show all -P1 -S10000")
        in_table = False
        luns = {}
        for line in stdout.readlines():
            if not in_table:
                if line.startswith('-------------'):
                    in_table = True
                continue
            else:
                (
                    lun_name,
                    lun_type,
                    raid,
                    size,
                    state,
                    cluster,
                    volume,
                ) = line.split()
                luns[lun_name] = volume

        stdin, stdout, stderr = ssh.exec_command("vsvr show")
        in_table = False
        server_list = []
        for line in stdout.readlines():
            if not in_table:
                if line.startswith('======='):
                    in_table = True
                continue
            else:
                no, state, server = line.split()
                if server.startswith('VS_MGMT'):
                    continue
                server_list.append(server)

        mounts = collections.defaultdict(list)
        for server in server_list:
            channel = ssh.invoke_shell()
            _command(channel, 'vsvr set %s' % server)
            lines = _command(channel, 'nfs cache show mounts')
            channel.close()
            if not lines:
                continue
            if lines[0].startswith('No Mount information'):
                continue
            for line in lines:
                if line.strip().endswith('>') or not line.strip():
                    continue
                try:
                    CLIENT, IP, ipaddr, SHARE, PATH, path = line.split(None, 6)
                except ValueError:
                    continue
                if '/' in path:
                    volume = path.split('/', 1)[1]
                else:
                    volume = path
                mounts[volume].append(ipaddr)
    finally:
        ssh.close()
    _save_shares(dev, luns, mounts)
    return name


@plugin.register(chain='discovery', requires=['ping', 'http'])
def ssh_onstor(**kwargs):
    if SSH_ONSTOR_USER is None or SSH_ONSTOR_PASSWORD is None:
        return False, 'no credentials.', kwargs
    if 'nx-os' in kwargs.get('snmp_name', '').lower():
        return False, 'incompatible Nexus found.', kwargs
    ip = str(kwargs['ip'])
    if kwargs.get('http_family') not in ('sscccc',):
        return False, 'no match.', kwargs
    if not network.check_tcp_port(ip, 22):
        DiscoveryWarning(
            message="Port 22 closed on an Onstor device.",
            plugin=__name__,
            ip=ip,
        ).save()
        return False, 'closed.', kwargs
    try:
        name = _run_ssh_onstor(ip)
    except (network.Error, Error, paramiko.SSHException) as e:
        DiscoveryWarning(
            message="This is an Onstor, but: " + str(e),
            plugin=__name__,
            ip=ip,
        ).save()
        return False, str(e), kwargs
    return True, name, kwargs
