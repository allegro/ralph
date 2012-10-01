#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import ssh as paramiko

from django.conf import settings
from lck.django.common import nested_commit_on_success

from ralph.util import network
from ralph.util import plugin
from ralph.discovery.models import (DeviceType, DeviceModel, Device, IPAddress,
                                    DiskShare, ComponentModel, ComponentType)
from ralph.discovery.hardware import normalize_wwn


SSH_3PAR_USER = settings.SSH_3PAR_USER
SSH_3PAR_PASSWORD = settings.SSH_3PAR_PASSWORD


class Error(Exception):
    pass


def _connect_ssh(ip):
    return network.connect_ssh(ip, SSH_3PAR_USER, SSH_3PAR_PASSWORD)

@nested_commit_on_success
def _save_shares(dev, shares):
    wwns = []
    for share_id, (label, wwn, snapshot_size, size, type,
                   speed, full) in shares.iteritems():
        wwn = normalize_wwn(wwn)
        wwns.append(wwn)
        model, created = ComponentModel.concurrent_get_or_create(
            name='3PAR %s disk share' % type, type=ComponentType.share.id,
            family=type, speed=speed)
        share, created = DiskShare.concurrent_get_or_create(wwn=wwn, device=dev)
        share.model = model
        share.label = label
        share.full = full
        share.size = size
        share.share_id = share_id
        share.snapshot_size = snapshot_size
        share.save()
    dev.diskshare_set.exclude(wwn__in=wwns).delete()

@nested_commit_on_success
def _save_device(ip, name, model_name, sn):
    model, model_created = DeviceModel.concurrent_get_or_create(
        name = '3PAR %s' % model_name, type=DeviceType.storage.id)
    dev, dev_created = Device.concurrent_get_or_create(sn=sn, model=model)
    dev.save()
    ipaddr, ip_created = IPAddress.concurrent_get_or_create(address=ip)
    ipaddr.device = dev
    ipaddr.is_management = True
    ipaddr.save()
    dev.management = ipaddr
    dev.save()
    return dev

def _run_ssh_3par(ip):
    ssh = _connect_ssh(ip)
    try:
        stdin, stdout, stderr = ssh.exec_command("showsys")
        lines = list(stdout.readlines())
        if not lines[1].startswith('  ID ---Name--- ---Model-'):
            raise Error('not a 3PAR.')
        line = lines[-1]
        name = line[5:15].strip()
        model_name = line[16:28].strip()
        sn = line[29:37].strip()
        stdin, stdout, stderr = ssh.exec_command("showvv -showcols Id,Name,VV_WWN,Snp_RawRsvd_MB,Usr_RawRsvd_MB,Prov")
        shares = {}
        for line in list(stdout.readlines()):
            if line.strip().startswith('Id'):
                continue
            if line.startswith('----'):
                break
            share_id, share_name, wwn, snapshot_size, size, prov = line.split(None, 5)
            if '--' in size or '--' in snapshot_size:
                continue
            share_id = int(share_id)
            if share_id == 0:
                continue
            snapshot_size = int(snapshot_size)
            size = int(size)

            stdin, stdout, stderr = ssh.exec_command("showld -p -vv %s" % share_name)
            lines = list(stdout.readlines())
            logical_id, logical_name, preserve, disk_type, speed = lines[1].split(None, 5)
            speed = int(speed) * 1000

            shares[share_id] = (share_name, wwn, snapshot_size, size,
                                disk_type, speed, prov.strip()=='full')
    finally:
        ssh.close()
    dev = _save_device(ip, name, model_name, sn)
    _save_shares(dev, shares)
    return name

@plugin.register(chain='discovery', requires=['ping', 'http', 'snmp'])
def ssh_3par(**kwargs):
    if SSH_3PAR_USER is None or SSH_3PAR_PASSWORD is None:
        return False, 'no credentials.', kwargs
    if 'nx-os' in kwargs.get('snmp_name', '').lower():
        return False, 'incompatible Nexus found.', kwargs
    ip = str(kwargs['ip'])
    if kwargs.get('http_family') not in ('Unspecified',):
        return False, 'no match.', kwargs
    if not kwargs.get('snmp_name').startswith('3PAR'):
        return False, 'no match.', kwargs
    if not network.check_tcp_port(ip, 22):
        return False, 'closed.', kwargs
    try:
        name = _run_ssh_3par(ip)
    except (network.Error, Error) as e:
        return False, str(e), kwargs
    except Error as e:
        return False, str(e), kwargs
    except paramiko.SSHException as e:
        return False, str(e), kwargs
    return True, name, kwargs

